"""
@relation(SDOC-LLR-208, SDOC-LLR-219, scope=file)
"""

import re
from pathlib import Path

import pytest

from strictdoc.core.project_templates import (
    PROJECT_TEMPLATE_EMPTY,
    PROJECT_TEMPLATE_HELLO_WORLD,
    PROJECT_TEMPLATE_TITLES,
    create_project_template,
)

MID_REGEX = re.compile(r"^MID: [a-f0-9]{32}$", re.MULTILINE)


def test_hello_world_template_creates_the_new_command_skeleton(
    tmp_path: Path,
) -> None:
    project_path = tmp_path / "project"
    project_template = create_project_template(
        PROJECT_TEMPLATE_HELLO_WORLD, project_path, 'My "quoted" project'
    )

    assert project_template.find_conflicts() == []
    project_template.write()

    assert sorted(
        str(path_.relative_to(project_path).as_posix())
        for path_ in project_path.rglob("*")
        if path_.is_file()
    ) == [
        "docs/high_level_requirements.sdoc",
        "docs/low_level_requirements.sdoc",
        "src/main.c",
        "strictdoc_config.py",
    ]
    config = (project_path / "strictdoc_config.py").read_text(encoding="utf-8")
    assert 'project_title="My \\"quoted\\" project",' in config
    compile(config, "strictdoc_config.py", "exec")
    hlr = (project_path / "docs" / "high_level_requirements.sdoc").read_text(
        encoding="utf-8"
    )
    assert len(MID_REGEX.findall(hlr)) == 2


def test_empty_template_creates_one_empty_document(tmp_path: Path) -> None:
    project_path = tmp_path / "empty_project"
    project_template = create_project_template(
        PROJECT_TEMPLATE_EMPTY, project_path, "Empty project"
    )
    project_template.write()

    document = (project_path / "docs" / "requirements.sdoc").read_text(
        encoding="utf-8"
    )
    assert document.startswith("[DOCUMENT]\n")
    assert len(MID_REGEX.findall(document)) == 1
    assert "[REQUIREMENT]" not in document
    config = (project_path / "strictdoc_config.py").read_text(encoding="utf-8")
    assert 'project_title="Empty project",' in config
    compile(config, "strictdoc_config.py", "exec")


def test_template_reports_existing_files_as_conflicts(tmp_path: Path) -> None:
    project_path = tmp_path / "project"
    (project_path / "docs").mkdir(parents=True)
    existing_document = project_path / "docs" / "requirements.sdoc"
    existing_document.write_text("existing", encoding="utf-8")

    project_template = create_project_template(
        PROJECT_TEMPLATE_EMPTY, project_path, "Project"
    )

    assert project_template.find_conflicts() == [existing_document]


def test_every_template_has_a_title() -> None:
    assert set(PROJECT_TEMPLATE_TITLES.keys()) == {
        PROJECT_TEMPLATE_HELLO_WORLD,
        PROJECT_TEMPLATE_EMPTY,
    }


def test_unknown_template_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown project template"):
        create_project_template("unknown", tmp_path, "Project")
