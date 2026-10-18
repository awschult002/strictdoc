"""
@relation(SDOC-LLR-220, SDOC-LLR-221, scope=file)
"""

import io
import os
import socket
import sys
import time
from pathlib import Path
from typing import Iterator, List

import pytest

from strictdoc.core.project_templates import (
    PROJECT_TEMPLATE_EMPTY,
    PROJECT_TEMPLATE_HELLO_WORLD,
)
from strictdoc.features.launcher.launcher_session import (
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    LauncherError,
    ServerExitedError,
    ServerProcess,
    add_recent_project,
    build_server_command,
    create_new_project,
    find_free_port,
    get_preferred_port,
    get_server_environment,
    is_port_free,
    is_strictdoc_project,
    normalize_recent_projects,
    validate_new_project_location,
)

HOST = DEFAULT_SERVER_HOST


@pytest.fixture
def busy_port() -> Iterator[int]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy_socket:
        busy_socket.bind((HOST, 0))
        busy_socket.listen(1)
        yield busy_socket.getsockname()[1]


def _get_unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
        test_socket.bind((HOST, 0))
        port: int = test_socket.getsockname()[1]
    return port


def _wait_until_port_is_free(port: int, timeout_seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if is_port_free(HOST, port):
            return True
        time.sleep(0.1)
    return False


def test_normalize_recent_projects_drops_invalid_and_duplicate_entries(
    tmp_path: Path,
) -> None:
    first_path = str(tmp_path / "first")
    second_path = str(tmp_path / "second")

    assert normalize_recent_projects(
        [first_path, 42, "", "   ", first_path, f" {second_path} "]
    ) == [first_path, second_path]
    assert normalize_recent_projects("not a list") == []
    assert normalize_recent_projects(None) == []


def test_normalize_recent_projects_limits_the_number_of_entries(
    tmp_path: Path,
) -> None:
    paths = [str(tmp_path / f"project_{index_}") for index_ in range(10)]

    assert normalize_recent_projects(paths, max_count=3) == paths[:3]


def test_add_recent_project_moves_the_project_to_the_top(
    tmp_path: Path,
) -> None:
    paths = [str(tmp_path / f"project_{index_}") for index_ in range(5)]

    recent_projects = add_recent_project(paths, paths[3], max_count=5)

    assert recent_projects == [paths[3], paths[0], paths[1], paths[2], paths[4]]


def test_add_recent_project_limits_the_number_of_entries(
    tmp_path: Path,
) -> None:
    paths = [str(tmp_path / f"project_{index_}") for index_ in range(5)]
    new_path = str(tmp_path / "new_project")

    recent_projects = add_recent_project(paths, new_path, max_count=5)

    assert recent_projects == [new_path, *paths[:4]]


@pytest.mark.parametrize(
    "file_name", ["strictdoc_config.py", "strictdoc.toml", "docs/a.sdoc"]
)
def test_is_strictdoc_project_detects_config_and_documents(
    tmp_path: Path, file_name: str
) -> None:
    file_path = tmp_path / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("", encoding="utf-8")

    assert is_strictdoc_project(str(tmp_path))


def test_is_strictdoc_project_ignores_hidden_and_output_folders(
    tmp_path: Path,
) -> None:
    for folder_name_ in (".git", "output"):
        (tmp_path / folder_name_).mkdir()
        (tmp_path / folder_name_ / "a.sdoc").write_text("", encoding="utf-8")
    (tmp_path / "readme.txt").write_text("", encoding="utf-8")

    assert not is_strictdoc_project(str(tmp_path))
    assert not is_strictdoc_project(str(tmp_path / "does_not_exist"))


def test_validate_new_project_location(tmp_path: Path) -> None:
    (tmp_path / "empty_folder").mkdir()
    (tmp_path / "full_folder").mkdir()
    (tmp_path / "full_folder" / "file.txt").write_text("", encoding="utf-8")
    (tmp_path / "file.txt").write_text("", encoding="utf-8")
    parent_path = str(tmp_path)

    assert validate_new_project_location(parent_path, "new_project") is None
    assert validate_new_project_location(parent_path, "empty_folder") is None
    assert validate_new_project_location(parent_path, "   ") is not None
    assert validate_new_project_location(parent_path, "a/b") is not None
    assert validate_new_project_location(parent_path, "..") is not None
    assert validate_new_project_location(parent_path, "full_folder") is not None
    assert validate_new_project_location(parent_path, "file.txt") is not None
    assert validate_new_project_location("", "new_project") is not None
    assert (
        validate_new_project_location(
            str(tmp_path / "does_not_exist"), "new_project"
        )
        is not None
    )


@pytest.mark.parametrize(
    "template_name", [PROJECT_TEMPLATE_HELLO_WORLD, PROJECT_TEMPLATE_EMPTY]
)
def test_create_new_project_creates_a_strictdoc_project(
    tmp_path: Path, template_name: str
) -> None:
    project_path = create_new_project(
        template_name, str(tmp_path / "My project")
    )

    assert project_path == str(tmp_path / "My project")
    assert is_strictdoc_project(project_path)
    config = Path(project_path, "strictdoc_config.py").read_text(
        encoding="utf-8"
    )
    assert 'project_title="My project",' in config


def test_create_new_project_refuses_to_overwrite_files(tmp_path: Path) -> None:
    create_new_project(PROJECT_TEMPLATE_EMPTY, str(tmp_path / "project"))

    with pytest.raises(LauncherError, match="Refusing to overwrite"):
        create_new_project(PROJECT_TEMPLATE_EMPTY, str(tmp_path / "project"))


def test_create_new_project_refuses_a_file_path(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("", encoding="utf-8")

    with pytest.raises(LauncherError, match="not a folder"):
        create_new_project(PROJECT_TEMPLATE_EMPTY, str(tmp_path / "file.txt"))


def test_find_free_port_returns_the_preferred_port_if_it_is_free() -> None:
    port = _get_unused_port()

    assert find_free_port(HOST, port) == port


def test_find_free_port_skips_a_busy_port(busy_port: int) -> None:
    port = find_free_port(HOST, busy_port)

    assert port != busy_port
    assert is_port_free(HOST, port)


def test_find_free_port_fails_when_no_port_is_free(busy_port: int) -> None:
    with pytest.raises(LauncherError, match="Could not find a free port"):
        find_free_port(HOST, busy_port, max_attempts=1)


def test_get_preferred_port_uses_explicit_port_then_project_config(
    tmp_path: Path,
) -> None:
    assert get_preferred_port(str(tmp_path), 6000) == 6000
    assert get_preferred_port(str(tmp_path), None) == DEFAULT_SERVER_PORT

    (tmp_path / "strictdoc_config.py").write_text(
        "from strictdoc.core.project_config import ProjectConfig\n"
        "\n"
        "def create_config() -> ProjectConfig:\n"
        "    return ProjectConfig(server_port=6123)\n",
        encoding="utf-8",
    )
    assert get_preferred_port(str(tmp_path), None) == 6123


def test_build_server_command_always_binds_the_given_host() -> None:
    command = build_server_command("/project", HOST, 6001)

    assert command[-6:] == [
        "server",
        "/project",
        "--host",
        HOST,
        "--port",
        "6001",
    ]


def test_server_environment_makes_strictdoc_importable() -> None:
    environment = get_server_environment()

    assert environment["PYTHONUNBUFFERED"] == "1"
    python_path = environment.get("PYTHONPATH", "")
    if python_path != os.environ.get("PYTHONPATH", ""):
        package_root = python_path.split(os.pathsep)[0]
        assert Path(package_root, "strictdoc", "__init__.py").is_file()


def _http_server_command(port: int) -> List[str]:
    return [
        sys.executable,
        "-m",
        "http.server",
        str(port),
        "--bind",
        HOST,
    ]


def test_server_process_waits_until_ready_and_stops(tmp_path: Path) -> None:
    port = _get_unused_port()
    server = ServerProcess(project_path=str(tmp_path), host=HOST, port=port)

    server.start(_http_server_command(port))
    try:
        assert server.wait_until_ready(timeout_seconds=30)
        assert server.is_running()
    finally:
        server.stop()

    assert not server.is_running()
    assert server.process is None
    assert _wait_until_port_is_free(port)


def test_server_process_reports_an_early_exit(tmp_path: Path) -> None:
    server = ServerProcess(project_path=str(tmp_path), host=HOST, port=1)

    server.start([sys.executable, "-c", "import sys; sys.exit(3)"])
    try:
        with pytest.raises(ServerExitedError) as exception_info:
            server.wait_until_ready(timeout_seconds=30)
    finally:
        server.stop()

    assert exception_info.value.return_code == 3


def test_server_process_wait_can_be_cancelled(tmp_path: Path) -> None:
    server = ServerProcess(project_path=str(tmp_path), host=HOST, port=1)

    server.start([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        assert not server.wait_until_ready(
            timeout_seconds=30, is_cancelled=lambda: True
        )
    finally:
        server.stop()


def test_server_process_stop_ends_child_processes(tmp_path: Path) -> None:
    port = _get_unused_port()
    # The server starts an HTTP server as its own child process and then
    # waits, like a server that starts worker processes.
    script = (
        "import subprocess, sys, time\n"
        f"subprocess.Popen({_http_server_command(port)!r})\n"
        "time.sleep(120)\n"
    )
    server = ServerProcess(project_path=str(tmp_path), host=HOST, port=port)

    server.start([sys.executable, "-c", script])
    try:
        assert server.wait_until_ready(timeout_seconds=30)
    finally:
        server.stop()

    assert _wait_until_port_is_free(port)


def test_server_process_forwards_output(tmp_path: Path) -> None:
    server = ServerProcess(project_path=str(tmp_path), host=HOST, port=1)

    server.start([sys.executable, "-c", "print('hello from the server')"])
    stream = server.get_output_stream()
    assert stream is not None
    output = io.StringIO(stream.read())
    server.stop()

    assert "hello from the server" in output.getvalue()
