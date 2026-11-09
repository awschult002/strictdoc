"""
Starter templates for new StrictDoc projects.

The "new" command and the desktop launcher create projects from these
templates.

@relation(SDOC-LLR-208, SDOC-LLR-219, scope=file)
"""

import json
from pathlib import Path
from typing import Dict, List

from strictdoc.helpers.mid import MID


class ProjectTemplate:
    def __init__(
        self,
        *,
        name: str,
        title: str,
        directories: List[Path],
        files: Dict[Path, str],
    ) -> None:
        self.name: str = name
        self.title: str = title
        self.directories: List[Path] = directories
        self.files: Dict[Path, str] = files

    def find_conflicts(self) -> List[Path]:
        """
        Return the template paths that already exist and would be overwritten.
        """
        conflicts: List[Path] = [
            directory_
            for directory_ in self.directories
            if directory_.exists() and not directory_.is_dir()
        ]
        conflicts.extend(
            file_path_ for file_path_ in self.files if file_path_.exists()
        )
        return conflicts

    def write(self) -> None:
        for directory_ in self.directories:
            directory_.mkdir(parents=True, exist_ok=True)
        for file_path_, content_ in self.files.items():
            file_path_.write_text(content_, encoding="utf-8")


PROJECT_TEMPLATE_HELLO_WORLD = "hello_world"
PROJECT_TEMPLATE_EMPTY = "empty"

PROJECT_TEMPLATE_TITLES: Dict[str, str] = {
    PROJECT_TEMPLATE_HELLO_WORLD: (
        "Hello world: linked high-level and low-level requirements, "
        "C source file"
    ),
    PROJECT_TEMPLATE_EMPTY: "Empty: one empty document",
}


def create_project_template(
    template_name: str, output_path: Path, project_title: str
) -> ProjectTemplate:
    if template_name == PROJECT_TEMPLATE_HELLO_WORLD:
        return create_hello_world_project_template(output_path, project_title)
    if template_name == PROJECT_TEMPLATE_EMPTY:
        return create_empty_project_template(output_path, project_title)
    raise ValueError(f"Unknown project template: {template_name}")


def create_hello_world_project_template(
    output_path: Path, project_title: str = "Hello World"
) -> ProjectTemplate:
    docs_path = output_path / "docs"
    src_path = output_path / "src"
    hlr_document_mid = MID.create()
    hlr_requirement_mid = MID.create()
    llr_document_mid = MID.create()
    llr_requirement_mid = MID.create()
    return ProjectTemplate(
        name=PROJECT_TEMPLATE_HELLO_WORLD,
        title=PROJECT_TEMPLATE_TITLES[PROJECT_TEMPLATE_HELLO_WORLD],
        directories=[output_path, docs_path, src_path],
        files={
            docs_path / "high_level_requirements.sdoc": (
                f"""\
[DOCUMENT]
MID: {hlr_document_mid}
TITLE: High-Level Requirements
PREFIX: HLR-
OPTIONS:
  ENABLE_MID: True

[REQUIREMENT]
MID: {hlr_requirement_mid}
UID: HLR-1
TITLE: Initial high-level requirement
STATEMENT: >>>
The system shall provide a hello world application.
<<<
"""
            ),
            docs_path / "low_level_requirements.sdoc": (
                f"""\
[DOCUMENT]
MID: {llr_document_mid}
TITLE: Low-Level Requirements
PREFIX: LLR-
OPTIONS:
  ENABLE_MID: True

[REQUIREMENT]
MID: {llr_requirement_mid}
UID: LLR-1
TITLE: Initial low-level requirement
STATEMENT: >>>
The software shall print a hello world message.
<<<
RELATIONS:
- TYPE: Parent
  VALUE: HLR-1
"""
            ),
            src_path / "main.c": (
                """\
/**
* @relation(LLR-1, scope=file)
*/
#include <stdio.h>

int main(void)
{
    printf("Hello, StrictDoc!\\n");
    return 0;
}
"""
            ),
            output_path / "strictdoc_config.py": (
                f"""\
from strictdoc.core.project_config import ProjectConfig


def create_config() -> ProjectConfig:
    return ProjectConfig(
        project_title={json.dumps(project_title)},
        project_features=[
            # Stable features.
            "TABLE_SCREEN",
            "TRACEABILITY_SCREEN",
            "DEEP_TRACEABILITY_SCREEN",
            "SEARCH",
            "TRACEABILITY_MATRIX_SCREEN",
            "REQUIREMENT_TO_SOURCE_TRACEABILITY",
            # "MATHJAX"

            # Experimental features.
            # "PROJECT_STATISTICS_SCREEN",
            # "TREE_MAP_SCREEN",
            # "REQIF",
            # "HTML2PDF",
            # "DIFF",
        ],
        include_doc_paths=[
            "/docs/",
        ],
        include_source_paths=[
            "/src/**",
        ],
    )
"""
            ),
        },
    )


def create_empty_project_template(
    output_path: Path, project_title: str
) -> ProjectTemplate:
    docs_path = output_path / "docs"
    document_mid = MID.create()
    return ProjectTemplate(
        name=PROJECT_TEMPLATE_EMPTY,
        title=PROJECT_TEMPLATE_TITLES[PROJECT_TEMPLATE_EMPTY],
        directories=[output_path, docs_path],
        files={
            docs_path / "requirements.sdoc": (
                f"""\
[DOCUMENT]
MID: {document_mid}
TITLE: Requirements
OPTIONS:
  ENABLE_MID: True
"""
            ),
            output_path / "strictdoc_config.py": (
                f"""\
from strictdoc.core.project_config import ProjectConfig


def create_config() -> ProjectConfig:
    return ProjectConfig(
        project_title={json.dumps(project_title)},
        project_features=[
            "TABLE_SCREEN",
            "TRACEABILITY_SCREEN",
            "DEEP_TRACEABILITY_SCREEN",
            "SEARCH",
        ],
        include_doc_paths=[
            "/docs/",
        ],
    )
"""
            ),
        },
    )
