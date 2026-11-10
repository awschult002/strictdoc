import os
import tempfile

import pytest

from strictdoc.backend.sdoc.sdoc_format import SDocFormat
from strictdoc.core.project_config import (
    ProjectConfig,
    ProjectConfigLoader,
    ProjectFeature,
    SavedQuery,
)
from strictdoc.features.html2pdf.html2pdf_format import HTML2PDFFormat


def test_01_default_config():
    project_config = ProjectConfig.default_config()
    assert project_config.include_source_paths == []


#
# Project features.
#
def test_10__project_features__accepts_strings_or_enums():
    project_config = ProjectConfig(
        project_features=[
            ProjectFeature.DIFF,
            ProjectFeature.HTML2PDF.value,
            "REQIF",
        ]
    )
    assert project_config.is_activated_diff()
    assert project_config.is_activated_html2pdf()
    assert project_config.is_activated_reqif()


def test_30_include_doc_paths_bad_mask():
    with pytest.raises(ValueError):
        _ = ProjectConfig(include_doc_paths=[" "])


def test_31_exclude_doc_paths_bad_mask():
    with pytest.raises(ValueError):
        _ = ProjectConfig(exclude_doc_paths=[" "])


def test_32_include_source_paths_bad_mask():
    with pytest.raises(ValueError):
        _ = ProjectConfig(include_source_paths=[" "])


def test_33_exclude_source_paths_bad_mask():
    with pytest.raises(ValueError):
        _ = ProjectConfig(exclude_source_paths=[" "])


#
# Editable document extensions.
#
def test_40_editable_document_extensions_only_sdoc():
    # SDocFormat is the base/always-available format, used here to test
    # the get_editable_document_extensions() mechanism itself (iterate
    # formats -> keep supports_edit() ones -> collect
    # supported_extensions()), independent of which formats a real
    # project happens to have configured.
    project_config = ProjectConfig(formats=[SDocFormat()])
    assert project_config.get_editable_document_extensions() == [".sdoc"]


def test_41_editable_document_extensions_excludes_non_editable_format():
    # HTML2PDFFormat is used (instead of a fake/stub Format) because it is
    # a real, permanently non-editable format: PDF output is exported
    # only, never edited through the UI, and supports_edit() is
    # guaranteed to stay False. This keeps the test meaningful without
    # inventing a throwaway Format subclass.
    project_config = ProjectConfig(formats=[SDocFormat(), HTML2PDFFormat()])
    extensions = project_config.get_editable_document_extensions()
    assert extensions == [".sdoc"]
    assert ".pdf" not in extensions


def test_60_valid_host_and_port():
    project_config = ProjectConfig(
        server_host="localhost123",
        server_port=5555,
    )
    assert project_config.server_host == "localhost123"
    assert project_config.server_port == 5555


def test_61_validate_invalid_host():
    with pytest.raises(AssertionError):
        _ = ProjectConfig(server_host="bad$host")


def test_62_validate_invalid_port():
    with pytest.raises(AssertionError):
        _ = ProjectConfig(server_port=1000000)


#
# Config loading from Python files.
#
def test_70_load_python_config_with_canonical_filename():
    config_content = """\
from strictdoc.core.project_config import ProjectConfig

def create_config():
    return ProjectConfig(project_title="Canonical")
"""
    with tempfile.NamedTemporaryFile(
        suffix="_strictdoc_config.py", mode="w", delete=False
    ) as f:
        f.write(config_content)
        path = f.name
    try:
        config = ProjectConfigLoader.load_from_path_or_get_default(
            path_to_config=path
        )
        assert config.project_title == "Canonical"
    finally:
        os.unlink(path)


def test_71_load_python_config_with_non_canonical_filename():
    config_content = """\
from strictdoc.core.project_config import ProjectConfig

def create_config():
    return ProjectConfig(project_title="NonCanonical")
"""
    with tempfile.NamedTemporaryFile(
        suffix="_my_custom_config.py", mode="w", delete=False
    ) as f:
        f.write(config_content)
        path = f.name
    try:
        config = ProjectConfigLoader.load_from_path_or_get_default(
            path_to_config=path
        )
        assert config.project_title == "NonCanonical"
    finally:
        os.unlink(path)


def test_80_lazy_document_loading_threshold_from_config(tmp_path):
    path_to_config = tmp_path / "strictdoc_config.py"
    path_to_config.write_text(
        """\
from strictdoc.core.project_config import ProjectConfig


def create_config():
    return ProjectConfig(lazy_document_loading_threshold=50)
"""
    )
    project_config = ProjectConfigLoader.load_from_path_or_get_default(
        path_to_config=str(path_to_config)
    )
    assert project_config.lazy_document_loading_threshold == 50


def test_81_lazy_document_loading_threshold_default_when_absent(tmp_path):
    path_to_config = tmp_path / "strictdoc_config.py"
    path_to_config.write_text(
        """\
from strictdoc.core.project_config import ProjectConfig


def create_config():
    return ProjectConfig(project_title="No threshold set")
"""
    )
    project_config = ProjectConfigLoader.load_from_path_or_get_default(
        path_to_config=str(path_to_config)
    )
    assert project_config.lazy_document_loading_threshold == 200


def test_82_lazy_document_loading_threshold_zero_disables():
    project_config = ProjectConfig(lazy_document_loading_threshold=0)
    assert project_config.lazy_document_loading_threshold == 0


def test_83_lazy_document_loading_threshold_negative_rejected():
    with pytest.raises(AssertionError):
        _ = ProjectConfig(lazy_document_loading_threshold=-1)


#
# Saved queries.
#
def test_90_saved_queries_default_to_empty_list():
    project_config = ProjectConfig()
    assert project_config.queries == []


def test_91_saved_queries_are_stored_and_looked_up_by_title():
    query = SavedQuery(title="Requirements", value="node.is_requirement")
    project_config = ProjectConfig(queries=[query])
    assert project_config.queries == [query]
    assert project_config.get_saved_query("Requirements") is query
    assert project_config.get_saved_query("Unknown") is None


def test_92_saved_queries_reject_empty_title():
    with pytest.raises(ValueError, match="title must not be empty"):
        _ = ProjectConfig(
            queries=[SavedQuery(title="  ", value="node.is_requirement")]
        )


def test_93_saved_queries_reject_duplicate_titles():
    with pytest.raises(ValueError, match="duplicate query title: 'Same'"):
        _ = ProjectConfig(
            queries=[
                SavedQuery(title="Same", value="node.is_requirement"),
                SavedQuery(title="Same", value="node.is_section"),
            ]
        )


def test_94_saved_queries_reject_value_that_does_not_parse():
    with pytest.raises(ValueError, match="query 'Broken' could not be parsed"):
        _ = ProjectConfig(
            queries=[SavedQuery(title="Broken", value="node.is_nothing(")]
        )


def test_95_saved_queries_reject_empty_value():
    with pytest.raises(ValueError, match="query 'Empty' has an empty value"):
        _ = ProjectConfig(queries=[SavedQuery(title="Empty", value="")])


def test_96_saved_queries_reject_items_that_are_not_saved_queries():
    with pytest.raises(ValueError, match="expected a SavedQuery"):
        _ = ProjectConfig(queries=[{"title": "A", "value": "node.is_section"}])


def test_97_saved_queries_load_from_python_config(tmp_path):
    path_to_config = tmp_path / "strictdoc_config.py"
    path_to_config.write_text(
        """\
from strictdoc.api import ProjectConfig, SavedQuery


def create_config():
    return ProjectConfig(
        queries=[
            SavedQuery(
                title="System requirements",
                value='(node.is_requirement and "System" in node["TITLE"])',
            ),
        ],
    )
"""
    )
    project_config = ProjectConfigLoader.load_from_path_or_get_default(
        path_to_config=str(path_to_config)
    )
    assert project_config.queries == [
        SavedQuery(
            title="System requirements",
            value='(node.is_requirement and "System" in node["TITLE"])',
        )
    ]
