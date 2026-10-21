"""
Tests for the Git Init and Clone actions of the launcher, written ahead of
the implementation. The tests use a local bare repository as the remote and
need no network.

The tests run against the API that git_action.py is expected to provide.
ASSUMED_API lists the names in one place. Until git_action.py has all of
them, the tests that use the API are skipped.

@relation(SDOC-LLR-220, scope=file)
"""

import http.server
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator, List

import pytest

# The API that the tests expect from strictdoc.features.launcher.git_action:
#
# get_available_git_actions(folder: str) -> Set[str]
#     The Git actions that the launcher menu shows for the folder. A subset
#     of ACTION_INIT, ACTION_CLONE, ACTION_PULL and ACTION_PUSH.
# get_git_work_tree_root(folder: str) -> Optional[str]
#     The root of the work tree that contains the folder, or None. Push and
#     pull run in this work tree.
# git_init(folder: str) -> result
#     Run "git init" in the folder.
# git_clone(url: str, folder: str) -> result
#     Run "git clone <url> ." in the folder with GIT_TERMINAL_PROMPT=0.
#
# The result has "ok" (bool) and "message" (str): a readable message, with
# git's own error text when git fails. The functions do not raise on a Git
# error.
ASSUMED_API = SimpleNamespace(
    module="strictdoc.features.launcher.git_action",
    get_available_git_actions="get_available_git_actions",
    get_git_work_tree_root="get_git_work_tree_root",
    git_init="git_init",
    git_clone="git_clone",
    action_init="ACTION_INIT",
    action_clone="ACTION_CLONE",
    action_pull="ACTION_PULL",
    action_push="ACTION_PUSH",
)

CLONE_TIMEOUT_SECONDS = 10.0


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


@pytest.fixture
def api() -> SimpleNamespace:
    module = pytest.importorskip(ASSUMED_API.module)
    names = [
        value
        for key, value in vars(ASSUMED_API).items()
        if key != "module"
    ]
    missing = [name for name in names if not hasattr(module, name)]
    if len(missing) > 0:
        pytest.skip(f"git_action.py does not provide: {', '.join(missing)}")
    return SimpleNamespace(
        **{
            key: getattr(module, value)
            for key, value in vars(ASSUMED_API).items()
            if key != "module"
        }
    )


@pytest.fixture(autouse=True)
def git_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Keep Git away from the user's configuration and credential helpers."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "StrictDoc Test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "test@example.com")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "StrictDoc Test")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "test@example.com")
    for name in ("GIT_ASKPASS", "SSH_ASKPASS", "GIT_DIR", "GIT_WORK_TREE"):
        monkeypatch.delenv(name, raising=False)
    if shutil.which("git") is None:
        pytest.skip("git is not installed")


@pytest.fixture
def remote(tmp_path: Path) -> Path:
    """A bare repository with one commit that contains a StrictDoc project."""
    remote_path = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "--initial-branch=main", str(remote_path))
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(seed, "init", "--initial-branch=main")
    (seed / "input.sdoc").write_text(
        "[DOCUMENT]\n"
        "TITLE: Cloned document\n"
        "\n"
        "[REQUIREMENT]\n"
        "UID: REQ-1\n"
        "STATEMENT: The system shall do something.\n",
        encoding="utf-8",
    )
    _git(seed, "add", ".")
    _git(seed, "commit", "-m", "Add a StrictDoc project")
    _git(seed, "push", str(remote_path), "main")
    return remote_path


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    return project


@pytest.fixture
def credential_server() -> Iterator[str]:
    """A local HTTP server that asks every request for credentials."""

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="test"')
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *_args: object) -> None:
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/remote.git"
    finally:
        server.shutdown()
        server.server_close()


def _list_folder(path: Path) -> List[str]:
    return sorted(os.listdir(path))


def test_bare_remote_fixture_can_be_cloned(
    remote: Path, tmp_path: Path
) -> None:
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", str(remote), str(clone))
    assert (clone / "input.sdoc").is_file()


def test_empty_folder_shows_init_and_clone_but_not_push(
    api: SimpleNamespace, folder: Path
) -> None:
    actions = api.get_available_git_actions(str(folder))

    assert api.action_init in actions
    assert api.action_clone in actions
    assert api.action_push not in actions
    assert api.action_pull not in actions


def test_init_creates_a_repository_and_shows_push_and_pull(
    api: SimpleNamespace, folder: Path
) -> None:
    result = api.git_init(str(folder))

    assert result.ok, result.message
    assert _git(folder, "rev-parse", "--is-inside-work-tree") == "true"
    actions = api.get_available_git_actions(str(folder))
    assert api.action_push in actions
    assert api.action_pull in actions
    assert api.action_init not in actions
    assert api.action_clone not in actions


def test_init_does_not_add_a_remote_or_a_commit(
    api: SimpleNamespace, folder: Path
) -> None:
    (folder / "input.sdoc").write_text(
        "[DOCUMENT]\nTITLE: T\n", encoding="utf-8"
    )

    result = api.git_init(str(folder))

    assert result.ok, result.message
    assert _git(folder, "remote") == ""
    log = subprocess.run(
        ["git", "log", "-1"],
        cwd=folder,
        capture_output=True,
        text=True,
        check=False,
    )
    assert log.returncode != 0


def test_initialized_folder_shows_push_and_hides_init(
    api: SimpleNamespace, folder: Path
) -> None:
    _git(folder, "init")

    actions = api.get_available_git_actions(str(folder))

    assert api.action_push in actions
    assert api.action_init not in actions
    assert api.action_clone not in actions


def test_project_in_a_parent_repository_hides_init_and_uses_the_parent(
    api: SimpleNamespace, tmp_path: Path
) -> None:
    parent = tmp_path / "parent"
    docs = parent / "docs"
    docs.mkdir(parents=True)
    _git(parent, "init")

    actions = api.get_available_git_actions(str(docs))

    assert api.action_init not in actions
    assert api.action_clone not in actions
    assert api.action_push in actions
    assert api.action_pull in actions
    work_tree_root = api.get_git_work_tree_root(str(docs))
    assert work_tree_root is not None
    assert Path(work_tree_root).resolve() == parent.resolve()


@pytest.mark.skipif(
    sys.platform == "win32" or os.geteuid() == 0,
    reason="needs POSIX permissions and a user that is not root",
)
def test_init_in_a_read_only_folder_reports_a_clean_error(
    api: SimpleNamespace, folder: Path
) -> None:
    folder.chmod(0o555)
    try:
        result = api.git_init(str(folder))
    finally:
        folder.chmod(0o755)

    assert not result.ok
    assert len(result.message.strip()) > 0
    assert "Traceback" not in result.message
    assert not (folder / ".git").exists()


def test_clone_into_an_empty_folder_puts_the_files_in_the_folder(
    api: SimpleNamespace, remote: Path, folder: Path
) -> None:
    result = api.git_clone(str(remote), str(folder))

    assert result.ok, result.message
    assert _list_folder(folder) == [".git", "input.sdoc"]
    assert Path(_git(folder, "rev-parse", "--show-toplevel")).resolve() == (
        folder.resolve()
    )


def test_clone_into_a_folder_that_is_not_empty_is_refused(
    api: SimpleNamespace, remote: Path, folder: Path
) -> None:
    existing = folder / "notes.txt"
    existing.write_text("Keep me.\n", encoding="utf-8")

    result = api.git_clone(str(remote), str(folder))

    assert not result.ok
    assert "empty" in result.message.lower()
    assert "Traceback" not in result.message
    assert _list_folder(folder) == ["notes.txt"]
    assert existing.read_text(encoding="utf-8") == "Keep me.\n"


def test_clone_from_a_bad_url_shows_the_git_error_and_leaves_the_folder_empty(
    api: SimpleNamespace, tmp_path: Path, folder: Path
) -> None:
    missing_remote = tmp_path / "missing.git"

    result = api.git_clone(str(missing_remote), str(folder))

    assert not result.ok
    # git's own error text, e.g. "fatal: repository '...' does not exist".
    assert "fatal:" in result.message
    assert "Traceback" not in result.message
    assert _list_folder(folder) == []


@pytest.mark.parametrize("url_kind", ["http_credentials", "file_missing"])
def test_clone_that_needs_credentials_does_not_hang(
    api: SimpleNamespace,
    credential_server: str,
    tmp_path: Path,
    folder: Path,
    url_kind: str,
) -> None:
    url = (
        credential_server
        if url_kind == "http_credentials"
        else (tmp_path / "missing.git").as_uri()
    )
    results: List[Any] = []

    def _clone() -> None:
        results.append(api.git_clone(url, str(folder)))

    started = time.monotonic()
    thread = threading.Thread(target=_clone, daemon=True)
    thread.start()
    thread.join(CLONE_TIMEOUT_SECONDS)
    elapsed = time.monotonic() - started

    assert not thread.is_alive(), (
        f"git_clone() still runs after {CLONE_TIMEOUT_SECONDS} s; "
        "it probably waits for a credential prompt."
    )
    assert elapsed < CLONE_TIMEOUT_SECONDS
    assert len(results) == 1
    assert not results[0].ok
    assert _list_folder(folder) == []


def test_credential_server_fixture_makes_plain_git_fail_without_prompt(
    credential_server: str, folder: Path
) -> None:
    completed = subprocess.run(
        ["git", "clone", credential_server, "."],
        cwd=folder,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        timeout=CLONE_TIMEOUT_SECONDS,
    )
    assert completed.returncode != 0
    assert _list_folder(folder) == []

