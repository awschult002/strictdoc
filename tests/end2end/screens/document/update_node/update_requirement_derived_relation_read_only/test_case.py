"""
@relation(SDOC-SRS-55, scope=file)
"""

from tests.end2end.e2e_case import E2ECase
from tests.end2end.end2end_test_setup import End2EndTestSetup
from tests.end2end.helpers.screens.project_index.screen_project_index import (
    Screen_ProjectIndex,
)
from tests.end2end.server import SDocTestServer


class Test(E2ECase):
    def test(self):
        test_setup = End2EndTestSetup(path_to_test_file=__file__)

        with SDocTestServer(
            input_path=test_setup.path_to_sandbox
        ) as test_server:
            self.open(test_server.get_host_and_port())

            screen_project_index = Screen_ProjectIndex(self)
            screen_project_index.assert_on_screen()
            screen_document = screen_project_index.do_click_on_first_document()
            screen_document.assert_on_screen_document()

            # The Child relation is stored on REQ-1. Editing REQ-2 shows the
            # derived Parent relation as a read-only row.
            child = screen_document.get_node(node_order=2)
            form_edit_requirement = child.do_open_form_edit_requirement()
            form_edit_requirement.do_open_tab("Relations")
            self.assert_element(
                "//*[@data-testid='requirement-form-derived-relation-row']"
            )
            self.assert_text(
                "(defined on REQ-1)",
                "//*[@data-testid='requirement-form-derived-relation-label']",
            )
            self.assert_element_not_present(
                "//*[@data-testid='requirement-form-relation-row']"
            )

            # The Edit button opens the edit form of REQ-1, the owner.
            self.click_xpath(
                "//*[@data-testid='form-action-edit-derived-relation']"
            )
            self.assert_element(
                "//*[@data-testid='requirement-form-relation-row']"
            )

        assert test_setup.compare_sandbox_and_expected_output()
