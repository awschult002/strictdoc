"""
The launcher's Export dialog passes an optional filter query to
"strictdoc export --filter-nodes".
"""

import subprocess
from types import SimpleNamespace
from typing import Any, List

import pytest

from strictdoc.commands.launcher_command import is_launcher_available

if not is_launcher_available():
    pytest.skip("tkinter is not available", allow_module_level=True)

from strictdoc.features.launcher import launcher_frame  # noqa: E402
from strictdoc.features.launcher.launcher_frame import (  # noqa: E402
    StrictDocLauncher,
)


def _run_export(monkeypatch: pytest.MonkeyPatch, filter_query: str) -> Any:
    calls: List[List[str]] = []
    errors: List[str] = []

    def _run(cmd: List[str], **_kwargs: object) -> Any:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1, "", "Invalid query")

    class _SyncThread:
        def __init__(self, target: Any, **_kwargs: object) -> None:
            self.target = target

        def start(self) -> None:
            self.target()

    monkeypatch.setattr(launcher_frame.subprocess, "run", _run)
    monkeypatch.setattr(launcher_frame.threading, "Thread", _SyncThread)
    fake_self = SimpleNamespace(
        workspace_dir="/project", after=lambda _ms, fn: fn()
    )
    StrictDocLauncher._run_export_thread(
        fake_self,  # type: ignore[arg-type]
        output_dir="/project/export",
        export_format="html",
        on_success=lambda: None,
        on_error=errors.append,
        filter_query=filter_query,
    )
    return calls[0], errors


def test_export_without_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    cmd, _ = _run_export(monkeypatch, "")
    assert "--filter-nodes" not in cmd
    assert cmd[-2:] == ["--output-dir", "/project/export"]


def test_export_with_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    query = 'node["STATUS"] == "Active"'
    cmd, errors = _run_export(monkeypatch, query)
    assert cmd[-2:] == ["--filter-nodes", query]
    assert "Invalid query" in errors[0]
