import io
import os
import sys
from pathlib import Path

import pytest

from strictdoc.features.launcher.launcher_entry import (
    LAUNCHER_PROGRAM_NAME,
    create_launcher_parser,
    ensure_standard_streams,
    get_launcher_arguments,
    run_launcher,
)


def test_launcher_arguments_skip_the_macos_process_serial_number() -> None:
    arguments = get_launcher_arguments(
        ["-psn_0_12345", "--project", "/project", "--no-browser"]
    )

    assert arguments == ["--project", "/project", "--no-browser"]


def test_launcher_parser_accepts_the_launcher_options() -> None:
    parser = create_launcher_parser()

    args = parser.parse_args(
        [
            "--new-project",
            "/new/project",
            "--template",
            "empty",
            "--port",
            "5200",
            "--no-browser",
        ]
    )

    assert parser.prog == LAUNCHER_PROGRAM_NAME
    assert args.project is None
    assert args.new_project == "/new/project"
    assert args.template == "empty"
    assert args.port == 5200
    assert args.no_browser is True
    assert args.no_window is False


def test_launcher_parser_rejects_project_and_new_project_together() -> None:
    parser = create_launcher_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--project", "/a", "--new-project", "/b"])


def test_run_launcher_reports_an_invalid_project_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stderr)
    missing_path = tmp_path / "missing"

    exit_code = run_launcher(["--project", str(missing_path), "--no-window"])

    assert exit_code == 1
    assert stderr.getvalue().startswith(
        "error: Provided project path does not exist or is not a folder: "
    )


def test_missing_standard_streams_are_replaced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)

    ensure_standard_streams()

    try:
        assert sys.stdout is not None
        assert sys.stderr is not None
        assert sys.stdout.name == os.devnull
        print("discarded", file=sys.stderr)  # noqa: T201
    finally:
        sys.stdout.close()
        sys.stderr.close()
