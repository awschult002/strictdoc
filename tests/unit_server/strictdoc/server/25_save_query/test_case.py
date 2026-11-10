import os
import shutil

import pytest
from fastapi.testclient import TestClient

from strictdoc.commands.server_config import ServerCommandConfig
from strictdoc.core.project_config import ProjectConfigLoader, SavedQuery
from strictdoc.server.app import create_app

PATH_TO_THIS_TEST_FOLDER = os.path.dirname(os.path.abspath(__file__))

SYSTEM_QUERY = '(node.is_requirement and "System" in node["TITLE"])'


@pytest.fixture
def project_path(tmp_path) -> str:
    # The test writes to the config file, so it runs on a copy.
    for file_name_ in ("sample.sdoc", "strictdoc_config.py"):
        shutil.copy(
            os.path.join(PATH_TO_THIS_TEST_FOLDER, file_name_), tmp_path
        )
    return str(tmp_path)


def create_client(project_path: str) -> TestClient:
    server_config = ServerCommandConfig(
        debug=False,
        command="server",
        input_path=project_path,
        output_path=os.path.join(project_path, "output"),
        config=os.path.join(project_path, "strictdoc_config.py"),
        reload=False,
        host="127.0.0.1",
        port=8001,
    )
    project_config = ProjectConfigLoader.load_using_server_config(server_config)
    return TestClient(create_app(project_config=project_config))


def test_01_save_button_is_shown_only_for_a_new_valid_query(project_path):
    client = create_client(project_path)

    response = client.get("/search")
    assert 'data-testid="save-query-form"' not in response.text

    response = client.get("/search", params={"q": SYSTEM_QUERY})
    assert 'data-testid="save-query-form"' in response.text

    # Already saved.
    response = client.get("/search", params={"q": "node.is_requirement"})
    assert 'data-testid="save-query-form"' not in response.text

    # Plain-text search is not a query that can be saved.
    response = client.get("/search", params={"q": "System"})
    assert 'data-testid="save-query-form"' not in response.text

    # Invalid query.
    response = client.get("/search", params={"q": "(node.is_requirement and"})
    assert 'data-testid="save-query-form"' not in response.text


def test_02_save_query_appends_to_config_and_updates_dropdown(project_path):
    client = create_client(project_path)

    response = client.post(
        "/actions/search/save_query",
        data={"q": SYSTEM_QUERY, "title": "System requirements"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == (
        "/search?q=%28node.is_requirement+and+%22System%22+in+"
        "node%5B%22TITLE%22%5D%29"
    )

    response = client.get(response.headers["location"])
    assert response.status_code == 200
    assert ">System requirements</option>" in response.text
    assert 'data-testid="save-query-form"' not in response.text

    with open(
        os.path.join(project_path, "strictdoc_config.py"), encoding="utf8"
    ) as file_:
        config_source = file_.read()
    assert "# Saved queries are appended below by the test." in config_source
    assert (
        "SavedQuery(title='System requirements', "
        'value=\'(node.is_requirement and "System" in node["TITLE"])\'),'
    ) in config_source

    reloaded_config = ProjectConfigLoader.load_from_python(
        config_py_path=os.path.join(project_path, "strictdoc_config.py")
    )
    assert reloaded_config.queries == [
        SavedQuery(title="All requirements", value="node.is_requirement"),
        SavedQuery(title="System requirements", value=SYSTEM_QUERY),
    ]


def test_03_save_query_rejects_duplicate_title(project_path):
    client = create_client(project_path)
    path_to_config = os.path.join(project_path, "strictdoc_config.py")
    with open(path_to_config, encoding="utf8") as file_:
        config_before = file_.read()

    response = client.post(
        "/actions/search/save_query",
        data={"q": SYSTEM_QUERY, "title": "All requirements"},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert (
        "A saved query with the title &#39;All requirements&#39; already exists."
    ) in response.text

    response = client.post(
        "/actions/search/save_query",
        data={"q": SYSTEM_QUERY, "title": "   "},
        follow_redirects=False,
    )
    assert response.status_code == 400
    assert "The query title must not be empty." in response.text

    with open(path_to_config, encoding="utf8") as file_:
        assert file_.read() == config_before
