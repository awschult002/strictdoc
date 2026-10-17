import os
from typing import Optional

from strictdoc.cli.base_command import CLIValidationError
from strictdoc.features.launcher.launcher_session import LauncherOptions


class LauncherCommandConfig:
    def __init__(
        self,
        *,
        project: Optional[str],
        new_project: Optional[str],
        template: str,
        port: Optional[int],
        no_browser: bool,
        no_window: bool,
    ) -> None:
        self.project_path: Optional[str] = project
        self.new_project_path: Optional[str] = new_project
        self.template: str = template
        self.port: Optional[int] = port
        self.open_browser: bool = not no_browser
        self.no_window: bool = no_window

    def validate(self) -> None:
        if self.project_path is not None and not os.path.isdir(
            self.project_path
        ):
            raise CLIValidationError(
                "Provided project path does not exist or is not a folder: "
                f"{self.project_path}"
            )
        if self.new_project_path is not None and (
            os.path.exists(self.new_project_path)
            and not os.path.isdir(self.new_project_path)
        ):
            raise CLIValidationError(
                "Provided new project path exists and is not a folder: "
                f"{self.new_project_path}"
            )
        if (
            self.no_window
            and self.project_path is None
            and self.new_project_path is None
        ):
            raise CLIValidationError(
                "The --no-window option requires --project or --new-project."
            )

    def create_launcher_options(self) -> LauncherOptions:
        return LauncherOptions(
            project_path=self.project_path,
            new_project_path=self.new_project_path,
            template=self.template,
            port=self.port,
            open_browser=self.open_browser,
        )
