import subprocess
import threading
from typing import Any, Callable, List, Tuple

import pytest

pytest.importorskip("tkinter")

from strictdoc.features.launcher import git_action  # noqa: E402


class _FakeLauncher:
    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = workspace_dir
        self.statuses: List[str] = []
        self.log: List[str] = []
        self.reported = threading.Event()
        self._callbacks: List[Callable[[], None]] = []

    def _ensure_workspace(self) -> bool:
        return True

    def set_status(self, text: str) -> None:
        self.statuses.append(text)

    def _append_log(self, text: str) -> None:
        self.log.append(text)

    def after(self, _ms: int, fn: Callable[[], None]) -> None:
        # Called from the real worker thread; hand the UI callback back to
        # the test thread instead of running Tk code off the main thread.
        self._callbacks.append(fn)
        self.reported.set()

    def run_pending_callbacks(self) -> None:
        for fn in self._callbacks:
            fn()


def test_commit_with_nothing_to_commit_is_not_a_failure(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(home / ".gitconfig"))
    monkeypatch.setenv("LC_ALL", "C")

    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True
        )

    git("init", "-q")
    git("config", "user.name", "Test User")
    git("config", "user.email", "test@example.invalid")
    git("config", "commit.gpgsign", "false")
    (repo / "file.txt").write_text("hello\n")
    git("add", "file.txt")
    git("commit", "-q", "-m", "initial")

    errors: List[Tuple[Any, ...]] = []
    infos: List[Tuple[Any, ...]] = []
    monkeypatch.setattr(
        git_action.messagebox, "showerror", lambda *a, **_k: errors.append(a)
    )
    monkeypatch.setattr(
        git_action.messagebox, "showinfo", lambda *a, **_k: infos.append(a)
    )
    monkeypatch.setattr(
        git_action.simpledialog,
        "askstring",
        lambda *_a, **_k: "Update from StrictDoc Launcher",
    )
    # No patching of threading or subprocess: the real worker thread runs
    # and we wait for it to report back through launcher.after().
    launcher = _FakeLauncher(str(repo))
    git_action._git_commit(launcher)
    assert launcher.reported.wait(timeout=60), "git commit worker timed out"
    launcher.run_pending_callbacks()

    assert errors == []
    assert not any("failed" in s for s in launcher.statuses)
    assert "Git commit completed." in launcher.statuses
    reported = "".join(launcher.log) + "".join(str(i) for i in infos)
    assert "nothing to commit" in reported
