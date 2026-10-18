"""
@relation(SDOC-LLR-220, scope=file)
"""

from pathlib import Path

import pytest

from strictdoc.cli.base_command import CLIValidationError
from strictdoc.cli.cli_arg_parser import SDocArgsParser
from strictdoc.cli.main import create_command_registry
from strictdoc.commands.launcher_command import LauncherCommand
from strictdoc.commands.launcher_config import LauncherCommandConfig


def _create_config(**overrides: object) -> LauncherCommandConfig:
    arguments: dict[str, object] = {
        "project": None,
        "new_project": None,
        "template": "hello_world",
        "port": None,
        "no_browser": False,
        "no_window": False,
    }
    arguments.update(overrides)
    return LauncherCommandConfig(**arguments)  # type: ignore[arg-type]


def test_config_without_options_is_valid() -> None:
    config = _create_config()

    config.validate()
    launcher_options = config.create_launcher_options()

    assert launcher_options.project_path is None
    assert launcher_options.new_project_path is None
    assert launcher_options.open_browser


def test_config_passes_the_options_to_the_launcher(tmp_path: Path) -> None:
    config = _create_config(
        project=str(tmp_path), port=6001, no_browser=True, template="empty"
    )

    config.validate()
    launcher_options = config.create_launcher_options()

    assert launcher_options.project_path == str(tmp_path)
    assert launcher_options.port == 6001
    assert launcher_options.template == "empty"
    assert not launcher_options.open_browser


def test_config_rejects_a_missing_project_folder(tmp_path: Path) -> None:
    config = _create_config(project=str(tmp_path / "does_not_exist"))

    with pytest.raises(CLIValidationError, match="does not exist"):
        config.validate()


def test_config_rejects_a_new_project_path_that_is_a_file(
    tmp_path: Path,
) -> None:
    (tmp_path / "file.txt").write_text("", encoding="utf-8")
    config = _create_config(new_project=str(tmp_path / "file.txt"))

    with pytest.raises(CLIValidationError, match="is not a folder"):
        config.validate()


def test_config_requires_a_project_without_window() -> None:
    config = _create_config(no_window=True)

    with pytest.raises(CLIValidationError, match="--no-window option requires"):
        config.validate()


def test_launcher_arguments_are_parsed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "strictdoc.cli.main.is_launcher_available", lambda: True
    )
    parser = SDocArgsParser.build_argparse(create_command_registry())

    args = parser.parse_args(
        [
            "launcher",
            "--new-project",
            str(tmp_path / "project"),
            "--template",
            "empty",
            "--port",
            "6002",
            "--no-browser",
        ]
    )
    command = LauncherCommand(args)

    assert command.config.new_project_path == str(tmp_path / "project")
    assert command.config.template == "empty"
    assert command.config.port == 6002
    assert not command.config.open_browser
    assert not command.config.no_window


def test_project_and_new_project_are_mutually_exclusive(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "strictdoc.cli.main.is_launcher_available", lambda: True
    )
    parser = SDocArgsParser.build_argparse(create_command_registry())

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "launcher",
                "--project",
                str(tmp_path),
                "--new-project",
                str(tmp_path / "project"),
            ]
        )
