"""
The windowed launcher executable of the bundle runs "strictdoc export" with
its own executable. That process has no console, so Python sets sys.stdout
and sys.stderr to None. HTML2PDF writes to sys.stderr and failed with
"'NoneType' object has no attribute 'write'".
"""

import sys
from typing import List

import pytest

from strictdoc.features.launcher import launcher_entry
from strictdoc.helpers import frozen


def test_strictdoc_command_gets_standard_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: List[object] = []

    def _run_strictdoc_command(_argv: List[str]) -> None:
        seen.append(sys.stdout)
        seen.append(sys.stderr)

    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(frozen, "mark_launcher_executable", lambda: None)
    monkeypatch.setattr(
        launcher_entry, "run_strictdoc_command", _run_strictdoc_command
    )

    launcher_entry.main([frozen.FROZEN_STRICTDOC_COMMAND, "export", "."])

    assert None not in seen


def test_multiprocessing_worker_gets_standard_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # freeze_support() runs a multiprocessing worker and exits without
    # returning, so the worker only gets the streams that were set before it.
    seen: List[object] = []

    def _freeze_support() -> None:
        seen.append(sys.stdout)
        seen.append(sys.stderr)
        raise SystemExit(0)

    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(
        launcher_entry.multiprocessing, "freeze_support", _freeze_support
    )

    with pytest.raises(SystemExit):
        launcher_entry.main(["--multiprocessing-fork"])

    assert len(seen) == 2
    assert None not in seen
    # html2pdf4doc calls fileno() on the streams when it is imported.
    for stream in seen:
        assert isinstance(stream.fileno(), int)  # type: ignore[attr-defined]
