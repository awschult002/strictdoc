"""
Launcher command for the Tk-based StrictDoc UI.

@relation(SDOC-SRS-208, SDOC-LLR-220, scope=file)
"""

import argparse
import importlib.util
import sys

from strictdoc.cli.argument_int_range import IntRange
from strictdoc.cli.base_command import BaseCommand, CLIValidationError
from strictdoc.commands.launcher_config import LauncherCommandConfig
from strictdoc.core.project_templates import (
    PROJECT_TEMPLATE_HELLO_WORLD,
    PROJECT_TEMPLATE_TITLES,
)
from strictdoc.features.launcher.launcher_session import (
    LauncherError,
    run_without_window,
)
from strictdoc.helpers.parallelizer import Parallelizer


def is_launcher_available() -> bool:
    return (
        importlib.util.find_spec("tkinter") is not None
        and importlib.util.find_spec("_tkinter") is not None
    )


class LauncherCommand(BaseCommand):
    HELP = "Launch StrictDoc's desktop launcher (experimental)."
    DETAILED_HELP = (
        "Launch StrictDoc's desktop launcher (experimental). Without options, "
        "the launcher opens a start dialog to open an existing project or "
        "create a new one. It then starts the StrictDoc server and opens the "
        "browser."
    )

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        project_group = parser.add_mutually_exclusive_group()
        project_group.add_argument(
            "--project",
            type=str,
            help="Open this project folder and start the server.",
        )
        project_group.add_argument(
            "--new-project",
            type=str,
            help=(
                "Create a new project in this folder from a starter template "
                "and start the server."
            ),
        )
        parser.add_argument(
            "--template",
            type=str,
            choices=list(PROJECT_TEMPLATE_TITLES.keys()),
            default=PROJECT_TEMPLATE_HELLO_WORLD,
            help=(
                "Starter template for --new-project "
                f"(default: {PROJECT_TEMPLATE_HELLO_WORLD})."
            ),
        )
        parser.add_argument(
            "--port",
            type=IntRange(1024, 65000),
            help=(
                "Preferred server port. If the port is busy, the launcher "
                "uses the next free port."
            ),
        )
        parser.add_argument(
            "--no-browser",
            default=False,
            action="store_true",
            help="Do not open the browser when the server is ready.",
        )
        # Runs the launcher flow without a window. Used by StrictDoc's own
        # tests on machines without a display, not intended for end users.
        parser.add_argument(
            "--no-window",
            default=False,
            action="store_true",
            help=argparse.SUPPRESS,
        )

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.config: LauncherCommandConfig = LauncherCommandConfig(
            project=args.project,
            new_project=args.new_project,
            template=args.template,
            port=args.port,
            no_browser=args.no_browser,
            no_window=args.no_window,
        )

    def run(self, parallelizer: Parallelizer) -> None:  # noqa: ARG002
        self.config.validate()
        launcher_options = self.config.create_launcher_options()

        if self.config.no_window:
            try:
                exit_code = run_without_window(launcher_options, sys.stdout)
            except LauncherError as launcher_error:
                raise CLIValidationError(str(launcher_error)) from None
            if exit_code != 0:
                sys.exit(exit_code)
            return

        # Delegate to the Tkinter launcher entry point.
        from strictdoc.features.launcher.launcher_frame import (  # noqa: PLC0415
            main as launcher_main,
        )

        launcher_main(launcher_options)
