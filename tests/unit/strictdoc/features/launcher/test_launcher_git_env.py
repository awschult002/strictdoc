import subprocess
from typing import Any, Dict, List

import pytest

pytest.importorskip("tkinter")

from strictdoc.features.launcher import git_action  # noqa: E402

CREATE_NO_WINDOW = 0x08000000


class _Recorder:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def __call__(self, argv: List[str], **kwargs: Any) -> Any:
        self.calls.append({"argv": list(argv), **kwargs})
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")


@pytest.fixture
def recorder(monkeypatch: pytest.MonkeyPatch) -> _Recorder:
    rec = _Recorder()
    monkeypatch.setattr(git_action.subprocess, "run", rec)
    return rec


def _run_init_and_clone(tmp_path: Any) -> None:
    init_dir = tmp_path / "init"
    init_dir.mkdir()
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    git_action.git_init(str(init_dir))
    git_action.git_clone("https://example.invalid/repo.git", str(clone_dir))


def _assert_safe(call: Dict[str, Any]) -> None:
    env = call["env"]
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GCM_INTERACTIVE"] == "never"
    assert "BatchMode=yes" in env["GIT_SSH_COMMAND"]
    assert call["stdin"] is subprocess.DEVNULL
    argv = call["argv"]
    assert not any(a.startswith("credential.helper=") for a in argv)
    assert "-c" not in argv


@pytest.mark.parametrize("windows", [False, True], ids=["posix", "windows"])
def test_init_and_clone_run_git_with_a_safe_environment(
    tmp_path: Any,
    recorder: _Recorder,
    monkeypatch: pytest.MonkeyPatch,
    windows: bool,
) -> None:
    if windows:
        monkeypatch.setattr(git_action.sys, "platform", "win32")
        monkeypatch.setattr(git_action.os, "name", "nt", raising=False)
        monkeypatch.setattr(
            git_action.subprocess,
            "CREATE_NO_WINDOW",
            CREATE_NO_WINDOW,
            raising=False,
        )
    else:
        monkeypatch.setattr(git_action.sys, "platform", "linux")
        monkeypatch.setattr(git_action.os, "name", "posix", raising=False)

    _run_init_and_clone(tmp_path)

    assert [c["argv"][1] for c in recorder.calls] == ["init", "clone"]
    for call in recorder.calls:
        _assert_safe(call)
        flags = call.get("creationflags", 0)
        if windows:
            assert flags & CREATE_NO_WINDOW
        else:
            assert not flags & CREATE_NO_WINDOW

    clone_argv = recorder.calls[1]["argv"]
    url = "https://example.invalid/repo.git"
    assert clone_argv.index("--") < clone_argv.index(url)


class _FakeLauncher:
    def __init__(self, folder: str) -> None:
        self.workspace_dir = folder

    def _ensure_workspace(self) -> bool:
        return True

    def set_status(self, _text: str) -> None:
        pass

    def _append_log(self, _text: str) -> None:
        pass

    def after(self, _ms: int, _fn: Any) -> None:
        pass


class _SyncThread:
    def __init__(self, target: Any, **_kwargs: Any) -> None:
        self._target = target

    def start(self) -> None:
        self._target()


@pytest.mark.parametrize("action", ["_git_pull", "_git_push"])
def test_pull_and_push_run_git_with_a_safe_environment(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    rec = _Recorder()

    def fake_run(argv: List[str], **kwargs: Any) -> Any:
        rec(argv, **kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout="true\n", stderr="")

    monkeypatch.setattr(git_action.subprocess, "run", fake_run)
    monkeypatch.setattr(git_action.threading, "Thread", _SyncThread)

    getattr(git_action, action)(_FakeLauncher(str(tmp_path)))

    assert rec.calls
    for call in rec.calls:
        _assert_safe({"env": {}, "stdin": None, **call})
