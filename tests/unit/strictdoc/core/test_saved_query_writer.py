from typing import List

import pytest

from strictdoc.core.project_config import (
    ProjectConfig,
    ProjectConfigLoader,
    SavedQuery,
)
from strictdoc.core.saved_query_writer import (
    SavedQueryWriteError,
    append_saved_query,
    save_query_to_project_config,
)

NEW_QUERY = "SavedQuery(title='New', value='node.is_section')"


def load_queries(tmp_path, source: str) -> List[SavedQuery]:
    path_to_config = tmp_path / "strictdoc_config.py"
    path_to_config.write_text(source)
    project_config = ProjectConfigLoader.load_from_python(
        config_py_path=str(path_to_config)
    )
    return project_config.queries


def test_01_appends_to_existing_multiline_list_with_trailing_comma():
    source = """\
from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(
        queries=[
            SavedQuery(title="Old", value="node.is_requirement"),
        ],
    )
"""
    assert append_saved_query(
        source, title="New", value="node.is_section"
    ) == source.replace(
        """\
            SavedQuery(title="Old", value="node.is_requirement"),
""",
        f"""\
            SavedQuery(title="Old", value="node.is_requirement"),
            {NEW_QUERY},
""",
    )


def test_02_adds_comma_after_last_item_without_trailing_comma():
    source = """\
from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(
        queries=[
            SavedQuery(title="Old", value="node.is_requirement")
        ]
    )
"""
    assert append_saved_query(source, title="New", value="node.is_section") == (
        source.replace(
            """\
            SavedQuery(title="Old", value="node.is_requirement")
""",
            f"""\
            SavedQuery(title="Old", value="node.is_requirement"),
            {NEW_QUERY},
""",
        )
    )


def test_03_appends_to_empty_list():
    source = """\
from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(queries=[])
"""
    assert append_saved_query(
        source, title="New", value="node.is_section"
    ) == source.replace("queries=[]", f"queries=[{NEW_QUERY}]")


def test_04_appends_to_empty_multiline_list():
    source = """\
from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(
        queries=[
        ],
    )
"""
    assert append_saved_query(
        source, title="New", value="node.is_section"
    ) == source.replace(
        "        queries=[\n        ],",
        f"        queries=[\n            {NEW_QUERY},\n        ],",
    )


def test_05_appends_to_single_line_list():
    source = """\
from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(queries=[SavedQuery(title="Old", value="node.is_requirement"),])
"""
    assert append_saved_query(
        source, title="New", value="node.is_section"
    ) == source.replace(
        '"node.is_requirement"),]',
        f'"node.is_requirement"), {NEW_QUERY}]',
    )


def test_06_adds_queries_keyword_to_multiline_call():
    source = """\
from strictdoc.core.project_config import ProjectConfig


def create_config() -> ProjectConfig:
    config = ProjectConfig(
        project_title="Project"
    )
    return config
"""
    assert append_saved_query(source, title="New", value="node.is_section") == (
        """\
from strictdoc.core.project_config import ProjectConfig
from strictdoc.api import SavedQuery


def create_config() -> ProjectConfig:
    config = ProjectConfig(
        project_title="Project",
        queries=[SavedQuery(title='New', value='node.is_section')],
    )
    return config
"""
    )


def test_07_adds_queries_keyword_to_single_line_and_empty_calls():
    source = """\
from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(project_title="Project")
"""
    assert append_saved_query(
        source, title="New", value="node.is_section"
    ) == source.replace(
        'project_title="Project")',
        f'project_title="Project", queries=[{NEW_QUERY}])',
    )

    source = source.replace('project_title="Project"', "")
    assert append_saved_query(
        source, title="New", value="node.is_section"
    ) == source.replace(
        "ProjectConfig()", f"ProjectConfig(queries=[{NEW_QUERY}])"
    )


def test_08_preserves_comments_and_formatting(tmp_path):
    source = """\
# The project config of the team.
from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    # Keep the queries sorted by topic.
    config = ProjectConfig(
        project_title = "Project",   # unusual spacing is kept
        queries=[
            # Safety.
            SavedQuery(title="Old", value="node.is_requirement"),  # a, b

            # Trailing comment before the bracket.
        ],
    )
    return config
"""
    result = append_saved_query(source, title="New", value="node.is_section")
    assert result.splitlines()[:12] == source.splitlines()[:12]
    assert result.splitlines()[12:] == [
        "            # Trailing comment before the bracket.",
        f"            {NEW_QUERY},",
        "        ],",
        "    )",
        "    return config",
    ]
    assert load_queries(tmp_path, result) == [
        SavedQuery(title="Old", value="node.is_requirement"),
        SavedQuery(title="New", value="node.is_section"),
    ]


def test_09_refuses_queries_that_are_not_a_list_literal():
    source = """\
from strictdoc.api import ProjectConfig, SavedQuery

QUERIES = [SavedQuery(title="Old", value="node.is_requirement")]


def create_config() -> ProjectConfig:
    return ProjectConfig(queries=QUERIES)
"""
    with pytest.raises(SavedQueryWriteError, match="not a list literal"):
        append_saved_query(source, title="New", value="node.is_section")


def test_10_refuses_config_without_create_config_or_project_config_call():
    with pytest.raises(SavedQueryWriteError, match="no create_config"):
        append_saved_query("x = 1\n", title="New", value="node.is_section")

    source = """\
def create_config():
    return make_config()
"""
    with pytest.raises(SavedQueryWriteError, match="exactly one ProjectConfig"):
        append_saved_query(source, title="New", value="node.is_section")


def test_11_quotes_and_backslashes_round_trip(tmp_path):
    source = """\
from strictdoc.api import ProjectConfig


def create_config() -> ProjectConfig:
    return ProjectConfig(
        queries=[],
    )
"""
    title = 'It\'s a "quoted" title with a \\ backslash and ünïcode'
    value = '"C:\\\\path" in node["TITLE"]'
    result = append_saved_query(source, title=title, value=value)
    assert load_queries(tmp_path, result) == [
        SavedQuery(title=title, value=value)
    ]


def test_12_keeps_windows_line_endings():
    source = (
        "from strictdoc.api import ProjectConfig, SavedQuery\r\n"
        "\r\n"
        "def create_config():\r\n"
        "    return ProjectConfig(\r\n"
        "        queries=[\r\n"
        '            SavedQuery(title="Old", value="node.is_requirement")\r\n'
        "        ],\r\n"
        "    )\r\n"
    )
    result = append_saved_query(source, title="New", value="node.is_section")
    assert "\n" not in result.replace("\r\n", "")
    assert f"            {NEW_QUERY},\r\n" in result


def create_project_config(tmp_path, source: str) -> ProjectConfig:
    path_to_config = tmp_path / "strictdoc_config.py"
    path_to_config.write_text(source)
    return ProjectConfigLoader.load_from_python(
        config_py_path=str(path_to_config)
    )


CONFIG_WITH_ONE_QUERY = """\
from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    return ProjectConfig(
        queries=[
            SavedQuery(title="Old", value="node.is_requirement"),
        ],
    )
"""


def test_20_save_query_writes_file_and_reloads_queries(tmp_path):
    project_config = create_project_config(tmp_path, CONFIG_WITH_ONE_QUERY)
    save_query_to_project_config(
        project_config, title=" New ", value=" node.is_section "
    )
    assert project_config.queries == [
        SavedQuery(title="Old", value="node.is_requirement"),
        SavedQuery(title="New", value="node.is_section"),
    ]
    assert NEW_QUERY in (tmp_path / "strictdoc_config.py").read_text()


@pytest.mark.parametrize(
    "title,value,error",
    [
        ("", "node.is_section", "must not be empty"),
        ("Old", "node.is_section", "'Old' already exists"),
        ("New", "node.is_section and", "could not be parsed"),
    ],
)
def test_21_save_query_rejects_bad_input_and_keeps_file(
    tmp_path, title, value, error
):
    project_config = create_project_config(tmp_path, CONFIG_WITH_ONE_QUERY)
    with pytest.raises(SavedQueryWriteError, match=error):
        save_query_to_project_config(project_config, title=title, value=value)
    assert (
        tmp_path / "strictdoc_config.py"
    ).read_text() == CONFIG_WITH_ONE_QUERY


def test_22_save_query_refuses_config_not_loaded_from_strictdoc_config_py():
    # The default config and a legacy strictdoc.toml config have no
    # strictdoc_config.py file to write to.
    project_config = ProjectConfig.default_config()
    assert project_config.config_py_path is None
    with pytest.raises(SavedQueryWriteError, match="strictdoc_config.py"):
        save_query_to_project_config(
            project_config, title="New", value="node.is_section"
        )


def test_23_save_query_undoes_the_change_if_reload_does_not_see_it(tmp_path):
    source = """\
from strictdoc.api import ProjectConfig, SavedQuery


def create_config() -> ProjectConfig:
    if False:
        return ProjectConfig(queries=[])
    return ProjectConfig.default_config()
"""
    project_config = create_project_config(tmp_path, source)
    with pytest.raises(SavedQueryWriteError, match="not found after reloading"):
        save_query_to_project_config(
            project_config, title="New", value="node.is_section"
        )
    assert (tmp_path / "strictdoc_config.py").read_text() == source
    assert project_config.queries == []
