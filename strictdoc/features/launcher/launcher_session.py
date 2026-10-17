"""
Launcher logic that does not depend on Tk.

This module keeps the list of recent projects, recognizes and creates
projects, and manages the StrictDoc server process that the launcher starts.

@relation(SDOC-LLR-220, SDOC-LLR-221, scope=file)
"""

import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import IO, Any, Callable, List, Optional

from strictdoc.core.project_templates import (
    PROJECT_TEMPLATE_HELLO_WORLD,
    create_project_template,
)
from strictdoc.helpers import frozen

DEFAULT_SERVER_HOST = "127.0.0.1"
DEFAULT_SERVER_PORT = 5111

# StrictDoc's project config accepts ports strictly between these values.
MIN_SERVER_PORT = 1025
MAX_SERVER_PORT = 64999

MAX_RECENT_PROJECTS = 5

STRICTDOC_CONFIG_FILE_NAMES = ("strictdoc_config.py", "strictdoc.toml")
STRICTDOC_DOCUMENT_EXTENSIONS = (".sdoc", ".sgra")

# Folders that never contain the documents of a project.
_IGNORED_FOLDER_NAMES = ("output", "node_modules", "__pycache__")

_PROJECT_NAME_REGEX = re.compile(r'^[^<>:"/\\|?*\x00-\x1f]+$')


class LauncherError(Exception):
    pass


class ServerExitedError(LauncherError):
    def __init__(self, return_code: int) -> None:
        super().__init__(
            f"The StrictDoc server stopped with exit code {return_code}."
        )
        self.return_code: int = return_code


class LauncherOptions:
    """
    Options that the "launcher" command passes to the launcher window.
    """

    def __init__(
        self,
        *,
        project_path: Optional[str] = None,
        new_project_path: Optional[str] = None,
        template: str = PROJECT_TEMPLATE_HELLO_WORLD,
        port: Optional[int] = None,
        open_browser: bool = True,
    ) -> None:
        self.project_path: Optional[str] = project_path
        self.new_project_path: Optional[str] = new_project_path
        self.template: str = template
        self.port: Optional[int] = port
        self.open_browser: bool = open_browser


def normalize_recent_projects(
    value: object, max_count: int = MAX_RECENT_PROJECTS
) -> List[str]:
    """
    Convert a stored value into a list of unique absolute paths.

    Entries that are not strings, empty strings and duplicates are dropped.
    """
    if not isinstance(value, list):
        return []
    result: List[str] = []
    for entry_ in value:
        if not isinstance(entry_, str):
            continue
        stripped_entry = entry_.strip()
        if len(stripped_entry) == 0:
            continue
        absolute_entry = os.path.abspath(stripped_entry)
        if absolute_entry in result:
            continue
        result.append(absolute_entry)
        if len(result) >= max_count:
            break
    return result


def add_recent_project(
    recent_projects: List[str],
    project_path: str,
    max_count: int = MAX_RECENT_PROJECTS,
) -> List[str]:
    """
    Put a project at the top of the recent projects and limit the list.
    """
    absolute_path = os.path.abspath(project_path)
    previous_projects = normalize_recent_projects(
        recent_projects, max_count=len(recent_projects) + 1
    )
    return [
        absolute_path,
        *[path_ for path_ in previous_projects if path_ != absolute_path],
    ][:max_count]


def is_strictdoc_project(path: str) -> bool:
    """
    Check whether a folder has a StrictDoc config file or any SDoc document.
    """
    if not os.path.isdir(path):
        return False
    for config_file_name_ in STRICTDOC_CONFIG_FILE_NAMES:
        if os.path.isfile(os.path.join(path, config_file_name_)):
            return True
    for _, folder_names, file_names in os.walk(path):
        folder_names[:] = [
            folder_name_
            for folder_name_ in folder_names
            if not folder_name_.startswith(".")
            and folder_name_ not in _IGNORED_FOLDER_NAMES
        ]
        for file_name_ in file_names:
            if file_name_.endswith(STRICTDOC_DOCUMENT_EXTENSIONS):
                return True
    return False


def validate_new_project_location(
    parent_path: str, project_name: str
) -> Optional[str]:
    """
    Return an error message, or None if a project can be created there.
    """
    stripped_name = project_name.strip()
    if len(stripped_name) == 0:
        return "Enter a project name."
    if (
        _PROJECT_NAME_REGEX.match(stripped_name) is None
        or stripped_name in (".", "..")
        or stripped_name.endswith((" ", "."))
    ):
        return (
            f"The project name '{stripped_name}' cannot be used as a folder "
            'name. Do not use the characters < > : " / \\ | ? *.'
        )
    if len(parent_path.strip()) == 0:
        return "Select the folder where the project is created."
    if not os.path.isdir(parent_path):
        return f"The folder does not exist: {parent_path}"
    project_path = os.path.join(parent_path, stripped_name)
    if os.path.exists(project_path):
        if not os.path.isdir(project_path):
            return f"A file with this name already exists: {project_path}"
        if len(os.listdir(project_path)) > 0:
            return f"The folder already exists and is not empty: {project_path}"
    return None


def create_new_project(
    template_name: str, project_path: str, project_title: Optional[str] = None
) -> str:
    """
    Create a project from a starter template and return its absolute path.

    Raises LauncherError if the project would overwrite existing files.
    """
    absolute_path = Path(os.path.abspath(project_path))
    if absolute_path.exists() and not absolute_path.is_dir():
        raise LauncherError(
            f"The path exists and is not a folder: {absolute_path}"
        )
    title = project_title if project_title is not None else absolute_path.name
    project_template = create_project_template(
        template_name, absolute_path, title
    )
    conflicts = project_template.find_conflicts()
    if len(conflicts) > 0:
        conflict_list = "\n".join(f"- {path_}" for path_ in conflicts)
        raise LauncherError(
            "Refusing to overwrite existing StrictDoc project files:\n"
            f"{conflict_list}"
        )
    project_template.write()
    return str(absolute_path)


def get_strictdoc_command() -> List[str]:
    """
    Return the command that runs StrictDoc's command-line interface.

    In a bundle, the command runs the bundled executable. See
    strictdoc/helpers/frozen.py.
    """
    return frozen.get_strictdoc_command()


def get_server_environment() -> dict[str, str]:
    """
    Return the environment for the server process.

    When StrictDoc runs from a source checkout instead of an installed
    package, the server needs the checkout on PYTHONPATH because it runs
    with the project folder as its working directory.
    """
    environment = {**os.environ, "PYTHONUNBUFFERED": "1"}
    if frozen.is_frozen():
        return environment
    import strictdoc  # noqa: PLC0415

    package_root = str(Path(strictdoc.__file__).resolve().parent.parent)
    if Path(package_root).name in ("site-packages", "dist-packages"):
        return environment
    python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        package_root
        if python_path is None or len(python_path) == 0
        else package_root + os.pathsep + python_path
    )
    return environment


def build_server_command(project_path: str, host: str, port: int) -> List[str]:
    return [
        *get_strictdoc_command(),
        "--debug",
        "server",
        project_path,
        "--host",
        host,
        "--port",
        str(port),
    ]


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
        # Without SO_REUSEADDR, a port in the TIME_WAIT state is reported as
        # busy on Linux and macOS even though the server could bind it.
        if sys.platform != "win32":
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            test_socket.bind((host, port))
        except OSError:
            return False
    return True


def find_free_port(
    host: str, preferred_port: int, max_attempts: int = 100
) -> int:
    """
    Return the preferred port if it is free, otherwise the next free port.

    Raises LauncherError if no free port is found.
    """
    port = min(max(preferred_port, MIN_SERVER_PORT), MAX_SERVER_PORT)
    for _ in range(max_attempts):
        if is_port_free(host, port):
            return port
        port = port + 1 if port < MAX_SERVER_PORT else MIN_SERVER_PORT
    raise LauncherError(
        f"Could not find a free port near {preferred_port} on {host}."
    )


def get_preferred_port(project_path: str, explicit_port: Optional[int]) -> int:
    """
    Return the explicit port, or else the port from the project config.
    """
    if explicit_port is not None:
        return explicit_port
    # Imported here: the project config module pulls in most of StrictDoc.
    from strictdoc.core.project_config import (  # noqa: PLC0415
        ProjectConfigLoader,
    )

    try:
        project_config = ProjectConfigLoader.load_from_path_or_get_default(
            path_to_config=project_path
        )
    except Exception:  # noqa: BLE001
        # A broken config is reported by the server itself when it starts.
        return DEFAULT_SERVER_PORT
    return project_config.server_port


def get_server_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/"


class ServerProcess:
    """
    A StrictDoc server that runs as a child process of the launcher.

    The server runs in its own process group (POSIX) or job object (Windows),
    so that stop() also ends the processes that the server has started.
    """

    def __init__(self, *, project_path: str, host: str, port: int) -> None:
        self.project_path: str = project_path
        self.host: str = host
        self.port: int = port
        self.url: str = get_server_url(host, port)
        self.process: Optional[subprocess.Popen[str]] = None
        self._windows_job: Optional[_WindowsJob] = None

    def start(self, command: Optional[List[str]] = None) -> None:
        server_command = (
            command
            if command is not None
            else build_server_command(self.project_path, self.host, self.port)
        )
        popen_options: dict[str, Any] = {}
        if sys.platform == "win32":
            popen_options["creationflags"] = (
                subprocess.CREATE_NO_WINDOW
                | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            popen_options["start_new_session"] = True
        self.process = subprocess.Popen(
            server_command,
            cwd=self.project_path,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=get_server_environment(),
            **popen_options,
        )
        if sys.platform == "win32":
            self._windows_job = _WindowsJob.create_for_process(self.process)

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def get_output_stream(self) -> Optional[IO[str]]:
        if self.process is None:
            return None
        return self.process.stdout

    def wait_until_ready(
        self,
        timeout_seconds: float = 300.0,
        poll_interval_seconds: float = 0.25,
        is_cancelled: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """
        Wait until the server answers HTTP requests.

        Returns False on timeout or cancellation. Raises ServerExitedError if
        the server process stops before it is ready.
        """
        assert self.process is not None, "The server has not been started."
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if is_cancelled is not None and is_cancelled():
                return False
            return_code = self.process.poll()
            if return_code is not None:
                raise ServerExitedError(return_code)
            if is_server_responding(self.url):
                return True
            time.sleep(poll_interval_seconds)
        return False

    def stop(self, timeout_seconds: float = 5.0) -> None:
        process = self.process
        if process is None:
            return
        try:
            if process.poll() is None:
                self._terminate(process)
                try:
                    process.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    self._kill(process)
                    process.wait(timeout=timeout_seconds)
            # Processes that the server started can outlive it.
            self._kill_remaining_processes(process)
        finally:
            if process.stdout is not None:
                process.stdout.close()
            if self._windows_job is not None:
                self._windows_job.close()
                self._windows_job = None
            self.process = None

    def _terminate(self, process: "subprocess.Popen[str]") -> None:
        if sys.platform == "win32":
            # The server has no console, so it cannot receive
            # CTRL_BREAK_EVENT. End the whole job, or at least the server.
            if self._windows_job is not None:
                self._windows_job.terminate()
            else:
                process.terminate()
        else:
            _signal_process_group(process, signal.SIGTERM)

    def _kill(self, process: "subprocess.Popen[str]") -> None:
        if sys.platform == "win32":
            process.kill()
        else:
            _signal_process_group(process, signal.SIGKILL)

    def _kill_remaining_processes(
        self, process: "subprocess.Popen[str]"
    ) -> None:
        if sys.platform == "win32":
            if self._windows_job is not None:
                self._windows_job.terminate()
        else:
            _signal_process_group(process, signal.SIGKILL)


def _signal_process_group(
    process: "subprocess.Popen[str]", signal_number: int
) -> None:
    if sys.platform != "win32":
        try:
            # The server is the leader of its own process group.
            os.killpg(process.pid, signal_number)
        except (ProcessLookupError, PermissionError):
            pass


def is_server_responding(url: str, timeout_seconds: float = 10.0) -> bool:
    # The server listens on a local address: never use a proxy for it.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url, timeout=timeout_seconds):
            return True
    except urllib.error.HTTPError:
        # Any HTTP response means that the server is listening.
        return True
    except (urllib.error.URLError, OSError):
        return False


def run_without_window(
    options: LauncherOptions,
    output: IO[str],
    host: str = DEFAULT_SERVER_HOST,
) -> int:
    """
    Run the launcher flow without the Tk window and return an exit code.

    The flow is the same as in the window: create or open the project, start
    the server on a free port, wait until it is ready, open the browser. The
    function returns when the server stops or the launcher is interrupted.
    """
    if options.new_project_path is not None:
        project_path = create_new_project(
            options.template, options.new_project_path
        )
        print(f"Created a new project: {project_path}", file=output, flush=True)
    else:
        assert options.project_path is not None
        project_path = os.path.abspath(options.project_path)

    port = find_free_port(host, get_preferred_port(project_path, options.port))
    server = ServerProcess(project_path=project_path, host=host, port=port)

    stop_requested = threading.Event()

    def _request_stop(_signal_number: int, _frame: Any) -> None:
        stop_requested.set()

    previous_sigterm_handler = signal.signal(signal.SIGTERM, _request_stop)
    previous_sigint_handler = signal.signal(signal.SIGINT, _request_stop)
    try:
        server.start()
        log_thread = _start_output_forwarding(server, output)
        try:
            is_ready = server.wait_until_ready(
                is_cancelled=stop_requested.is_set
            )
        except ServerExitedError as server_exited_error:
            log_thread.join(timeout=5)
            print(f"error: {server_exited_error}", file=output, flush=True)
            return 1
        if not is_ready:
            if stop_requested.is_set():
                return 0
            print(
                "error: The StrictDoc server did not become ready in time.",
                file=output,
                flush=True,
            )
            return 1
        print(
            f"StrictDoc server is ready: {server.url}", file=output, flush=True
        )
        if options.open_browser:
            webbrowser.open(server.url)
        while not stop_requested.is_set() and server.is_running():
            stop_requested.wait(0.25)
        if not stop_requested.is_set() and server.process is not None:
            return_code = server.process.poll()
            if return_code is not None and return_code != 0:
                log_thread.join(timeout=5)
                print(
                    f"error: {ServerExitedError(return_code)}",
                    file=output,
                    flush=True,
                )
                return 1
        return 0
    finally:
        server.stop()
        signal.signal(signal.SIGTERM, previous_sigterm_handler)
        signal.signal(signal.SIGINT, previous_sigint_handler)
        print("StrictDoc server stopped.", file=output, flush=True)


def _start_output_forwarding(
    server: ServerProcess, output: IO[str]
) -> threading.Thread:
    stream = server.get_output_stream()

    def _forward() -> None:
        if stream is None:
            return
        try:
            for line_ in stream:
                output.write(line_)
                output.flush()
        except (OSError, ValueError):
            # The stream is closed when the server stops.
            pass

    thread = threading.Thread(target=_forward, daemon=True)
    thread.start()
    return thread


class _WindowsJob:
    """
    A Windows job object that ends all its processes when it is closed.

    If the launcher itself is killed, Windows closes the job handle and ends
    the server together with its child processes.
    """

    def __init__(self, handle: int) -> None:
        self._handle: Optional[int] = handle

    @staticmethod
    def create_for_process(
        process: "subprocess.Popen[str]",
    ) -> Optional["_WindowsJob"]:
        if sys.platform == "win32":
            handle = _create_windows_job_handle(process)
            return _WindowsJob(handle) if handle is not None else None
        else:
            return None

    def terminate(self) -> None:
        if sys.platform == "win32":
            if self._handle is not None:
                _terminate_windows_job(self._handle)

    def close(self) -> None:
        if sys.platform == "win32":
            if self._handle is not None:
                _close_windows_job(self._handle)
                self._handle = None


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _IoCounters(ctypes.Structure):
        _fields_ = [
            (name_, ctypes.c_ulonglong)
            for name_ in (
                "ReadOperationCount",
                "WriteOperationCount",
                "OtherOperationCount",
                "ReadTransferCount",
                "WriteTransferCount",
                "OtherTransferCount",
            )
        ]

    class _BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _BasicLimitInformation),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000

    def _get_kernel32() -> Any:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.CreateJobObjectW.argtypes = [
            ctypes.c_void_p,
            wintypes.LPCWSTR,
        ]
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.AssignProcessToJobObject.argtypes = [
            wintypes.HANDLE,
            wintypes.HANDLE,
        ]
        kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        return kernel32

    def _create_windows_job_handle(
        process: "subprocess.Popen[str]",
    ) -> Optional[int]:
        kernel32 = _get_kernel32()
        handle = kernel32.CreateJobObjectW(None, None)
        if handle is None or handle == 0:
            return None
        limit_information = _ExtendedLimitInformation()
        limit_information.BasicLimitInformation.LimitFlags = (
            _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        is_configured = kernel32.SetInformationJobObject(
            handle,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limit_information),
            ctypes.sizeof(limit_information),
        )
        # Popen keeps the Windows process handle in this private attribute.
        process_handle = getattr(process, "_handle", None)
        if (
            is_configured == 0
            or process_handle is None
            or kernel32.AssignProcessToJobObject(handle, int(process_handle))
            == 0
        ):
            kernel32.CloseHandle(handle)
            return None
        return int(handle)

    def _terminate_windows_job(handle: int) -> None:
        _get_kernel32().TerminateJobObject(handle, 1)

    def _close_windows_job(handle: int) -> None:
        _get_kernel32().CloseHandle(handle)
