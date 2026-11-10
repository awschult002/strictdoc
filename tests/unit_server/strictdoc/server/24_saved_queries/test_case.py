import os
import re

import pytest
from fastapi.testclient import TestClient

from strictdoc.commands.server_config import ServerCommandConfig
from strictdoc.core.project_config import ProjectConfig, ProjectConfigLoader
from strictdoc.server.app import create_app

PATH_TO_THIS_TEST_FOLDER = os.path.dirname(os.path.abspath(__file__))
PATH_TO_CONFIG = os.path.join(PATH_TO_THIS_TEST_FOLDER, "strictdoc_config.py")
assert os.path.exists(PATH_TO_CONFIG)


@pytest.fixture(scope="module")
def client() -> TestClient:
    server_config = ServerCommandConfig(
        debug=False,
        command="server",
        input_path=PATH_TO_THIS_TEST_FOLDER,
        output_path=os.path.join(PATH_TO_THIS_TEST_FOLDER, "output"),
        config=PATH_TO_CONFIG,
        reload=False,
        host="127.0.0.1",
        port=8001,
    )
    project_config: ProjectConfig = (
        ProjectConfigLoader.load_using_server_config(server_config)
    )
    return TestClient(create_app(project_config=project_config))


def test_01_search_screen_lists_saved_queries(client: TestClient) -> None:
    response = client.get("/search")
    assert response.status_code == 200
    assert 'data-testid="saved-queries-select"' in response.text
    assert ">System requirements</option>" in response.text
    assert ">All requirements</option>" in response.text
    # The query value is HTML-escaped inside the option's value attribute.
    assert (
        'value="(node.is_requirement and &#34;System&#34; in '
        'node[&#34;TITLE&#34;])"'
    ) in response.text


def test_02_saved_query_matching_current_search_is_selected(
    client: TestClient,
) -> None:
    response = client.get("/search", params={"q": "node.is_requirement"})
    assert response.status_code == 200
    assert "Found <b>2</b> results." in response.text
    assert re.search(
        r'value="node\.is_requirement"[^>]*selected\s*>All requirements</option>',
        response.text,
    )
    assert "disabled selected" not in response.text


def test_03_search_screen_hides_dropdown_without_saved_queries() -> None:
    server_config = ServerCommandConfig(
        debug=False,
        command="server",
        input_path=PATH_TO_THIS_TEST_FOLDER,
        output_path=os.path.join(PATH_TO_THIS_TEST_FOLDER, "output"),
        config=None,
        reload=False,
        host="127.0.0.1",
        port=8001,
    )
    project_config = ProjectConfig(project_features=["SEARCH"])
    project_config.integrate_server_config(server_config)
    client = TestClient(create_app(project_config=project_config))
    response = client.get("/search")
    assert response.status_code == 200
    assert "saved-queries-select" not in response.text
