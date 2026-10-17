"""
Tests for the launcher window. They need Tk and a display, and they start a
real StrictDoc server.

@relation(SDOC-LLR-220, SDOC-LLR-221, scope=file)
"""

import gc
import os
import signal
import socket
import sys
import time
from pathlib import Path
from typing import Callable, Dict, Iterator, List

import pytest

from strictdoc.commands.launcher_command import is_launcher_available

if not is_launcher_available():
    pytest.skip("tkinter is not available", allow_module_level=True)
if sys.platform.startswith("linux") and len(os.environ.get("DISPLAY", "")) == 0:
    pytest.skip("no display (DISPLAY is not set)", allow_module_level=True)

import tkinter as tk  # noqa: E402

from strictdoc.features.launcher import launcher_frame  # noqa: E402
from strictdoc.features.launcher.launcher_frame import (  # noqa: E402
    StrictDocLauncher,
)
from strictdoc.features.launcher.launcher_session import (  # noqa: E402
    LauncherOptions,
    is_port_free,
)

HOST = "127.0.0.1"


@pytest.fixture(autouse=True)
def collect_tk_garbage() -> Iterator[None]:
    """
    Collect the Tk objects of a test in the main thread.

    Tk variables and images call Tcl when Python deletes them. If the garbage
    collector deletes them later in a background thread of another test, Tcl
    crashes the process.
    """
    yield
    gc.collect()


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Dict[str, object]:
    """Keep the launcher settings in memory instead of the user profile."""
    stored_settings: Dict[str, object] = {}

    def _load(_self: StrictDocLauncher) -> Dict[str, object]:
        return dict(stored_settings)

    def _save(_self: StrictDocLauncher, value: Dict[str, object]) -> None:
        stored_settings.clear()
        stored_settings.update(value)

    monkeypatch.setattr(StrictDocLauncher, "_load_launcher_settings", _load)
    monkeypatch.setattr(StrictDocLauncher, "_save_launcher_settings", _save)
    return stored_settings


@pytest.fixture
def opened_urls(monkeypatch: pytest.MonkeyPatch) -> List[str]:
    urls: List[str] = []
    monkeypatch.setattr(launcher_frame.webbrowser, "open", urls.append)
    monkeypatch.setattr(
        launcher_frame.messagebox, "showerror", _fail_on_message_box
    )
    return urls


@pytest.fixture
def project_path(tmp_path: Path) -> Iterator[Path]:
    project = tmp_path / "project"
    project.mkdir()
    (project / "input.sdoc").write_text(
        "[DOCUMENT]\n"
        "TITLE: Launcher test document\n"
        "\n"
        "[REQUIREMENT]\n"
        "UID: REQ-1\n"
        "STATEMENT: The system shall do something.\n",
        encoding="utf-8",
    )
    yield project


def _fail_on_message_box(title: str, message: str, **_kwargs: object) -> None:
    raise AssertionError(f"Unexpected message box: {title}: {message}")


def _get_unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
        test_socket.bind((HOST, 0))
        port: int = test_socket.getsockname()[1]
    return port


def _create_launcher(options: LauncherOptions) -> StrictDocLauncher:
    try:
        return StrictDocLauncher(options)
    except tk.TclError as tcl_error:
        pytest.skip(f"Tk cannot open a window: {tcl_error}")


def _process_events_until(
    launcher: StrictDocLauncher,
    condition: Callable[[], bool],
    timeout_seconds: float = 60.0,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        launcher.update()
        if condition():
            return True
        time.sleep(0.05)
    return False


def test_launcher_opens_a_project_starts_the_server_and_stops_it(
    project_path: Path,
    settings: Dict[str, object],
    opened_urls: List[str],
) -> None:
    port = _get_unused_port()
    launcher = _create_launcher(
        LauncherOptions(project_path=str(project_path), port=port)
    )
    try:
        assert _process_events_until(
            launcher, lambda: launcher._server_ready
        ), "The server did not become ready."
        assert launcher.server_port == port
        assert opened_urls == [f"http://{HOST}:{port}/"]
        assert str(launcher.server_btn.cget("text")) == "Stop server"
        launcher_section = settings["launcher"]
        assert isinstance(launcher_section, dict)
        assert launcher_section["recent_workspaces"] == [str(project_path)]

        launcher.stop_server()

        assert launcher.server_process is None
        assert str(launcher.server_btn.cget("text")) == "Start server"
        assert _process_events_until(
            launcher, lambda: is_port_free(HOST, port), timeout_seconds=15
        )
    finally:
        launcher._shutdown()


def test_launcher_creates_a_new_project_without_opening_a_browser(
    tmp_path: Path,
    settings: Dict[str, object],  # noqa: ARG001
    opened_urls: List[str],
) -> None:
    new_project_path = tmp_path / "new_project"
    launcher = _create_launcher(
        LauncherOptions(
            new_project_path=str(new_project_path),
            template="hello_world",
            port=_get_unused_port(),
            open_browser=False,
        )
    )
    try:
        assert _process_events_until(
            launcher, lambda: launcher._server_ready
        ), "The server did not become ready."
        assert (new_project_path / "strictdoc_config.py").is_file()
        assert launcher.workspace_dir == str(new_project_path)
        assert opened_urls == []
    finally:
        launcher._shutdown()


def test_launcher_shows_the_start_dialog_without_a_project(
    settings: Dict[str, object],  # noqa: ARG001
    opened_urls: List[str],  # noqa: ARG001
) -> None:
    launcher = _create_launcher(LauncherOptions())
    try:
        start_dialogs: List[tk.Misc] = []

        def _find_start_dialog() -> bool:
            start_dialogs[:] = [
                child_
                for child_ in launcher.winfo_children()
                if isinstance(child_, launcher_frame.StartDialog)
            ]
            return len(start_dialogs) == 1

        assert _process_events_until(
            launcher, _find_start_dialog, timeout_seconds=10
        )
        assert launcher.state() == "withdrawn"

        start_dialog = start_dialogs[0]
        assert isinstance(start_dialog, launcher_frame.StartDialog)
        start_dialog.dismiss()
        launcher.update()

        assert launcher.state() != "withdrawn"
        assert launcher.server_process is None
    finally:
        launcher._shutdown()


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows has no SIGTERM handler support"
)
def test_launcher_stops_the_server_on_sigterm(
    project_path: Path,
    settings: Dict[str, object],  # noqa: ARG001
    opened_urls: List[str],  # noqa: ARG001
) -> None:
    port = _get_unused_port()
    launcher = _create_launcher(
        LauncherOptions(
            project_path=str(project_path), port=port, open_browser=False
        )
    )
    original_handler = signal.getsignal(signal.SIGTERM)
    previous_handlers = launcher.install_signal_handlers()
    destroyed: List[bool] = []
    launcher.bind(
        "<Destroy>",
        lambda event_: (
            destroyed.append(True) if event_.widget is launcher else None
        ),
    )
    try:
        assert previous_handlers[signal.SIGTERM] is original_handler
        assert _process_events_until(
            launcher, lambda: launcher._server_ready
        ), "The server did not become ready."

        os.kill(os.getpid(), signal.SIGTERM)

        assert _process_events_until(
            launcher, lambda: len(destroyed) > 0, timeout_seconds=15
        ), "The launcher did not close on SIGTERM."
        assert launcher.server_process is None
        assert is_port_free(HOST, port)
    finally:
        launcher_frame.restore_signal_handlers(previous_handlers)
        if len(destroyed) == 0:
            launcher._shutdown()

    assert signal.getsignal(signal.SIGTERM) is original_handler
