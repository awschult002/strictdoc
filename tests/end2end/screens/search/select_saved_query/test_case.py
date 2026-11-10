import os

from tests.end2end.e2e_case import E2ECase
from tests.end2end.helpers.screens.project_index.screen_project_index import (
    Screen_ProjectIndex,
)
from tests.end2end.helpers.screens.search.search import Screen_Search
from tests.end2end.server import SDocTestServer

path_to_this_test_file_folder = os.path.dirname(os.path.abspath(__file__))


class Test(E2ECase):
    def test(self):
        with SDocTestServer(
            input_path=path_to_this_test_file_folder
        ) as test_server:
            self.open(test_server.get_host_and_port())

            screen_project_index = Screen_ProjectIndex(self)
            screen_project_index.assert_on_screen()

            screen_search: Screen_Search = (
                screen_project_index.do_click_on_search_screen_link()
            )
            screen_search.assert_on_screen("search")

            screen_search_results = screen_search.do_select_saved_query(
                "System requirements"
            )
            screen_search_results.assert_nr_results(1)
            screen_search_results.assert_text("System requirement statement.")
            screen_search_results.assert_no_text(
                "Logging requirement statement."
            )
            self.assert_attribute(
                "//input[@id='q']",
                "value",
                '(node.is_requirement and "System" in node["TITLE"])',
                by="xpath",
            )

            screen_search_results = screen_search.do_select_saved_query(
                "All requirements"
            )
            screen_search_results.assert_nr_results(2)
