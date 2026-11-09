"""
@relation(SDOC-LLR-208, scope=file)
"""

import argparse
from pathlib import Path

from strictdoc.cli.base_command import BaseCommand, CLIValidationError
from strictdoc.core.project_templates import (
    create_hello_world_project_template,
)
from strictdoc.helpers.parallelizer import Parallelizer


class NewCommand(BaseCommand):
    HELP = "Create an initial StrictDoc project."
    DETAILED_HELP = HELP

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "input_path",
            type=str,
            help="Folder where the initial StrictDoc project is created.",
        )

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args

    def run(self, parallelizer: Parallelizer) -> None:  # noqa: ARG002
        output_path = Path(self.args.input_path)
        if output_path.exists() and not output_path.is_dir():
            raise CLIValidationError(
                "error: "
                "Provided path exists and is not a directory: "
                f"'{output_path}'"
            )

        project_template = create_hello_world_project_template(output_path)
        conflicts = project_template.find_conflicts()
        if len(conflicts) > 0:
            conflict_list = "\n".join(f"- {path}" for path in conflicts)
            raise CLIValidationError(
                "Refusing to overwrite existing StrictDoc project files:\n"
                f"{conflict_list}"
            )

        project_template.write()

        print(  # noqa: T201
            f"""\
+============================================================+
|            StrictDoc project skeleton created              |
+============================================================+

Location: {output_path}

Next steps:

1. Change into the project directory

   cd {output_path}

2. Export static HTML documentation

   strictdoc export .

3. Start the web server

   strictdoc server .
"""
        )
