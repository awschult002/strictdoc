"""
Entry point of the windowed launcher executable in the StrictDoc bundle.

The PyInstaller spec scripts/strictdoc.spec builds this module into the
"strictdoc_launcher" executable (and into StrictDoc.app on macOS). The
executable runs the desktop launcher. When the launcher starts StrictDoc
commands, the executable runs them as "strictdoc_launcher _strictdoc <args>".

The executable has no console on Windows and macOS, so this module does not
use strictdoc.cli.main for the launcher. strictdoc.cli.main replaces
sys.stdout with file descriptor 1, which does not exist without a console.

@relation(SDOC-LLR-222, scope=file)
"""

import argparse
import multiprocessing
import os
import sys
from typing import List, Optional

from strictdoc.cli.base_command import CLIValidationError
from strictdoc.commands.launcher_command import LauncherCommand
from strictdoc.helpers import frozen
from strictdoc.helpers.parallelizer import Parallelizer

LAUNCHER_PROGRAM_NAME = "strictdoc_launcher"


def get_launcher_arguments(argv: List[str]) -> List[str]:
    """
    Return the launcher arguments without the arguments of the system.

    Older macOS versions start an app with a "-psn_<number>" argument.
    """
    return [argument for argument in argv if not argument.startswith("-psn_")]


def create_launcher_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=LAUNCHER_PROGRAM_NAME,
        description=LauncherCommand.DETAILED_HELP,
    )
    LauncherCommand.add_arguments(parser)
    return parser


def ensure_standard_streams() -> None:
    """
    Replace missing standard streams with streams that discard the output.

    A windowed executable that starts without a console has no stdout and no
    stderr. Python sets sys.stdout and sys.stderr to None in this case.
    """
    if sys.stdout is None:
        sys.stdout = open(  # noqa: SIM115
            os.devnull, "w", encoding="utf-8"
        )
    if sys.stderr is None:
        sys.stderr = open(  # noqa: SIM115
            os.devnull, "w", encoding="utf-8"
        )


def run_launcher(argv: List[str]) -> int:
    """
    Run the launcher with the command-line arguments and return an exit code.
    """
    parser = create_launcher_parser()
    args = parser.parse_args(get_launcher_arguments(argv))
    command = LauncherCommand(args)
    parallelizer = Parallelizer.create(False)
    try:
        command.run(parallelizer)
    except CLIValidationError as validation_error:
        print(f"error: {validation_error}", file=sys.stderr, flush=True)  # noqa: T201
        return 1
    finally:
        parallelizer.shutdown()
    return 0


def run_strictdoc_command(argv: List[str]) -> None:  # pragma: no cover
    """
    Run StrictDoc's command-line interface with the arguments.
    """
    from strictdoc.cli.main import main as strictdoc_main  # noqa: PLC0415

    sys.argv = ["strictdoc", *argv]
    strictdoc_main()


def main(argv: Optional[List[str]] = None) -> None:  # pragma: no cover
    # A worker process of multiprocessing starts this executable again with
    # the arguments of multiprocessing. freeze_support() runs the worker and
    # exits.
    multiprocessing.freeze_support()
    # A windowed executable has no console, so sys.stdout and sys.stderr
    # are None in the launcher and in every StrictDoc command it starts.
    ensure_standard_streams()
    frozen.mark_launcher_executable()
    frozen.run_frozen_helper_command_if_requested()

    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 0 and arguments[0] == frozen.FROZEN_STRICTDOC_COMMAND:
        run_strictdoc_command(arguments[1:])
        return

    sys.exit(run_launcher(arguments))


if __name__ == "__main__":  # pragma: no cover
    main()
