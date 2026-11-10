import argparse
import os
from typing import Optional

from strictdoc.cli.base_command import BaseCommand, CLIValidationError
from strictdoc.core.project_config import ProjectConfigLoader
from strictdoc.helpers.parallelizer import Parallelizer


class QueriesCommand(BaseCommand):
    HELP = "Print the queries saved in the project config."
    DETAILED_HELP = """\
Print the title and value of each query saved in the "queries" list of the
project config. A saved query can be used with "strictdoc export --query
<title>" or selected on the Search screen.
"""

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "input_path",
            type=str,
            nargs="?",
            default=".",
            help="Path to the project tree.",
        )
        parser.add_argument(
            "--config",
            type=str,
            help="Path to the StrictDoc config file.",
        )

    def __init__(self, args: argparse.Namespace) -> None:
        self.input_path: str = args.input_path
        self.config_path: Optional[str] = args.config

    def run(self, parallelizer: Parallelizer) -> None:  # noqa: ARG002
        if not os.path.exists(self.input_path):
            raise CLIValidationError(
                f"Provided input path does not exist: {self.input_path}"
            )
        path_to_config = self.config_path
        if path_to_config is None:
            path_to_config = self.input_path
            if os.path.isfile(path_to_config):
                path_to_config = os.path.dirname(path_to_config)
        elif not os.path.exists(path_to_config):
            raise CLIValidationError(
                "Provided path to a configuration file does not exist: "
                f"{path_to_config}"
            )
        project_config = ProjectConfigLoader.load_from_path_or_get_default(
            path_to_config=path_to_config
        )
        if len(project_config.queries) == 0:
            print("No saved queries found in the project config.")  # noqa: T201
            return
        for query_ in project_config.queries:
            print(f"{query_.title}\n    {query_.value}")  # noqa: T201
