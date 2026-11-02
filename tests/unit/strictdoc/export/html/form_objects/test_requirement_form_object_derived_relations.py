from pathlib import Path

from strictdoc.core.project_config import ProjectConfig
from strictdoc.core.traceability_index_builder import TraceabilityIndexBuilder
from strictdoc.export.html.form_objects.requirement_form_object import (
    RequirementFormObject,
)
from strictdoc.helpers.parallelizer import NullParallelizer

SDOC_TEMPLATE = """\
[DOCUMENT]
TITLE: Doc

[GRAMMAR]
ELEMENTS:
- TAG: REQUIREMENT
  FIELDS:
  - TITLE: UID
    TYPE: String
    REQUIRED: False
  - TITLE: TITLE
    TYPE: String
    REQUIRED: False
  RELATIONS:
  - TYPE: Parent
  - TYPE: Child
  - TYPE: Parent
    ROLE: Refines

[REQUIREMENT]
UID: REQ-1
TITLE: Parent
{req1_relations}
[REQUIREMENT]
UID: REQ-2
TITLE: Child
{req2_relations}"""


def _forms(tmp_path: Path, req1_relations: str, req2_relations: str):
    (tmp_path / "doc.sdoc").write_text(
        SDOC_TEMPLATE.format(
            req1_relations=req1_relations, req2_relations=req2_relations
        )
    )
    project_config = ProjectConfig.default_config()
    project_config.input_paths = [str(tmp_path)]
    project_config.output_dir = str(tmp_path / "output")
    traceability_index = TraceabilityIndexBuilder.create(
        project_config=project_config, parallelizer=NullParallelizer()
    )
    forms = {}
    for uid in ("REQ-1", "REQ-2"):
        node = traceability_index.get_node_by_uid(uid)
        forms[uid] = RequirementFormObject.create_from_requirement(
            requirement=node,
            revision=1,
            context_document_mid=node.get_document().reserved_mid,
            traceability_index=traceability_index,
        )
    return forms


def _editable(form):
    return [(f.field_type.value, f.field_value) for f in form.reference_fields]


def _derived(form):
    return [
        (d.relation_type, d.owner_uid, d.role) for d in form.derived_relations
    ]


def test_case_a_parent_stored_on_child(tmp_path):
    forms = _forms(tmp_path, "", "RELATIONS:\n- TYPE: Parent\n  VALUE: REQ-1\n")
    assert _editable(forms["REQ-2"]) == [("Parent", "REQ-1")]
    assert _derived(forms["REQ-2"]) == []
    assert _editable(forms["REQ-1"]) == []
    assert _derived(forms["REQ-1"]) == [("Child", "REQ-2", None)]


def test_case_b_child_stored_on_parent(tmp_path):
    forms = _forms(tmp_path, "RELATIONS:\n- TYPE: Child\n  VALUE: REQ-2\n", "")
    assert _editable(forms["REQ-1"]) == [("Child", "REQ-2")]
    assert _derived(forms["REQ-1"]) == []
    assert _editable(forms["REQ-2"]) == []
    assert _derived(forms["REQ-2"]) == [("Parent", "REQ-1", None)]
    # Derived rows are never submitted, so saving REQ-2 cannot touch them.
    assert forms["REQ-2"].reference_fields == []


def test_role_is_kept(tmp_path):
    forms = _forms(
        tmp_path,
        "",
        "RELATIONS:\n- TYPE: Parent\n  VALUE: REQ-1\n  ROLE: Refines\n",
    )
    assert _derived(forms["REQ-1"]) == [("Child", "REQ-2", "Refines")]


def test_no_index_means_no_derived_rows(tmp_path):
    (tmp_path / "doc.sdoc").write_text(
        SDOC_TEMPLATE.format(req1_relations="", req2_relations="")
    )
    project_config = ProjectConfig.default_config()
    project_config.input_paths = [str(tmp_path)]
    project_config.output_dir = str(tmp_path / "output")
    traceability_index = TraceabilityIndexBuilder.create(
        project_config=project_config, parallelizer=NullParallelizer()
    )
    node = traceability_index.get_node_by_uid("REQ-1")
    form = RequirementFormObject.create_from_requirement(
        requirement=node,
        revision=1,
        context_document_mid=node.get_document().reserved_mid,
    )
    assert form.derived_relations == []
