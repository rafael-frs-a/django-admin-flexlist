import re
import time
from dataclasses import dataclass
from unittest.case import TestCase

import pytest
from playwright.sync_api import Page, expect
from playwright.sync_api._generated import Locator


@dataclass
class FieldCard:
    description: str
    visible: bool


class AppTestCase(TestCase):
    @pytest.fixture(autouse=True)
    def _setup_fixtures(self, page: Page, app_url: str, page_timeout: int) -> None:
        self.page = page
        self.app_url = app_url
        self.page_timeout = page_timeout

        self.admin_username = "jon.doe"
        self.staff_username = "jane.doe"

        self.sleep_interval = 1  # seconds

    def _navigate_to(self, path: str) -> None:
        self.page.goto(f"{self.app_url}{path}")

    def _check_url(self, url: str) -> None:
        expect(self.page).to_have_url(re.compile(url), timeout=self.page_timeout)

    def _login(self, username: str) -> None:
        self._navigate_to("/admin/")
        self.page.get_by_label("Username").fill(username)
        self.page.get_by_label("Password").fill(
            username
        )  # The password is the same as the username
        self.page.get_by_role("button", name="Log in").click()
        expect(
            self.page.get_by_role("heading", name="Site administration")
        ).to_be_visible()

    def _logout(self) -> None:
        logout_button = self.page.get_by_role("button", name="Log out")

        if logout_button.count() == 0:
            logout_button = self.page.get_by_role("link", name="Log out")

        logout_button.click()
        expect(self.page.get_by_role("heading", name="Logged out")).to_be_visible()

    def _get_card_container(self) -> Locator:
        return self.page.locator("#daf-edit-layout-fields-container")

    def _open_edit_layout_form(self) -> None:
        self.page.get_by_role("link", name="Edit layout").click()
        expect(self.page.get_by_role("heading", name="Edit Layout")).to_be_visible()

    def _get_expected_button_text(self, field_card: FieldCard) -> str:
        return "Hide" if field_card.visible else "Show"

    def _check_field_cards(self, expected_fields: list[FieldCard]) -> None:
        container = self._get_card_container()
        cards = container.locator("div.daf-field-card")

        assert cards.count() == len(expected_fields)

        for idx, expected_field in enumerate(expected_fields):
            card = cards.nth(idx)
            content = card.locator("div.daf-field-card-content")
            expect(content).to_have_text(expected_field.description, ignore_case=True)
            expected_button_text = self._get_expected_button_text(expected_field)
            expect(
                card.get_by_role("button", name=expected_button_text)
            ).to_be_visible()

    def _get_field_card(self, field_description: str) -> Locator:
        container = self._get_card_container()
        return container.locator("div.daf-field-card", has_text=field_description)

    def _copy_fields(self, fields: list[FieldCard]) -> list[FieldCard]:
        return [FieldCard(field.description, field.visible) for field in fields]

    def _toggle_field_card(
        self, fields: list[FieldCard], field_description: str
    ) -> list[FieldCard]:
        fields_copy = self._copy_fields(fields)
        field_card = next(
            field for field in fields_copy if field.description == field_description
        )

        card = self._get_field_card(field_description)
        expected_button_text = self._get_expected_button_text(field_card)
        card.get_by_role("button", name=expected_button_text).click()
        field_card.visible = not field_card.visible
        expected_button_text = self._get_expected_button_text(field_card)
        toggle_button = card.get_by_role("button", name=expected_button_text)
        expect(toggle_button).to_be_visible()

        # Let's check that the "Show" button has a custom background color
        if expected_button_text == "Show":
            background_color = toggle_button.evaluate(
                "node => getComputedStyle(node).backgroundColor"
            )
            assert background_color == "rgb(204, 255, 204)"

        return fields_copy

    def _drag_field_card(
        self, original_fields: list[FieldCard], source_idx: int, target_idx: int
    ) -> list[FieldCard]:
        fields = self._copy_fields(original_fields)
        source_field_card = fields[source_idx]
        target_field_card = fields[target_idx]
        fields = (
            fields[source_idx : source_idx + 1]  # noqa: E203
            + fields[:source_idx]  # noqa: E203
            + fields[source_idx + 1 :]  # noqa: E203
        )
        source = self._get_field_card(source_field_card.description)
        target = self._get_field_card(target_field_card.description)
        source.drag_to(target)
        return fields

    def _change_fields(self, original_fields: list[FieldCard]) -> list[FieldCard]:
        fields = self._toggle_field_card(original_fields, "First name")
        fields = self._toggle_field_card(fields, "Last name")
        # Let's drag the 3rd card to the top
        return self._drag_field_card(fields, 2, 0)

    def _check_list_view_fields(self, expected_fields: list[FieldCard]) -> None:
        # Let's check if all expected original fields are visible and follow the correct order
        thead = self.page.locator("#result_list thead")
        skip = 1  # Skip the checkbox column
        visible_fields = [field for field in expected_fields if field.visible]
        assert thead.locator("th").count() == len(visible_fields) + skip

        for idx, expected_field in enumerate(visible_fields, start=skip):
            th = thead.locator("th").nth(idx)
            expect(th).to_have_text(expected_field.description)

    def _test_users_change_list(self, username: str) -> None:
        # Navigate to users page
        self._navigate_to("/admin/users/user/")
        expect(
            self.page.get_by_role("heading", name="Select user to change")
        ).to_be_visible()

        expected_fields = [
            FieldCard("Username", True),
            FieldCard("Full name", True),
            FieldCard("Email address", True),
            FieldCard("DOB", True),
            FieldCard("First name", True),
            FieldCard("Last name", True),
            FieldCard("Staff status", True),
            FieldCard("Superuser status", True),
            FieldCard("Active", True),
            FieldCard("Date joined", True),
        ]

        if username == self.admin_username:
            # Field that is only visible to admins
            expected_fields.append(FieldCard("Last login", True))

        self._check_list_view_fields(expected_fields)

        # Open the edit layout form and check if all expected fields are visible
        self._open_edit_layout_form()
        self._check_field_cards(expected_fields)

        # The form dialog is still open. Let's change some fields, cancel, and check that the changes were not saved
        self._change_fields(expected_fields)
        self.page.get_by_role("button", name="Cancel").click()
        self._open_edit_layout_form()
        self._check_field_cards(expected_fields)

        # The form dialog is still open. Let's change the fields again, save, and check that the changes were saved
        changed_fields = self._change_fields(expected_fields)
        self.page.get_by_role("button", name="Save").click()
        time.sleep(self.sleep_interval)  # Wait for the page to reload
        expect(
            self.page.get_by_role("heading", name="Select user to change")
        ).to_be_visible()
        self._check_list_view_fields(changed_fields)
        self._open_edit_layout_form()
        self._check_field_cards(changed_fields)
        self.page.get_by_role("button", name="Cancel").click()

        # Let's refresh the page and check the changes again
        self.page.reload()
        expect(
            self.page.get_by_role("heading", name="Select user to change")
        ).to_be_visible()
        self._check_list_view_fields(changed_fields)
        self._open_edit_layout_form()
        self._check_field_cards(changed_fields)
        self.page.get_by_role("button", name="Cancel").click()

    def _check_model_list_fields(self, expected_fields: list[FieldCard]) -> None:
        # Let's check if all expected original models are visible and follow the correct order
        tbody = self.page.locator("div.app-blog.module.current-app tbody")
        visible_fields = [field for field in expected_fields if field.visible]
        assert tbody.locator("th").count() == len(visible_fields)

        for idx, expected_field in enumerate(visible_fields):
            th = tbody.locator("th").nth(idx)
            expect(th).to_have_text(expected_field.description)

    def _change_models(self, original_fields: list[FieldCard]) -> list[FieldCard]:
        fields = self._toggle_field_card(original_fields, "Comments")
        # Let's drag the 3rd card to the top
        return self._drag_field_card(fields, 2, 0)

    def _test_blog_app_index(self, username: str) -> None:
        # Navigate to blog app index page
        self._navigate_to("/admin/blog/")
        expect(
            self.page.get_by_role("heading", name="Blog administration")
        ).to_be_visible()

        expected_fields = [
            FieldCard("Comments", True),
            FieldCard("Posts", True),
            FieldCard("Tags", True),
        ]

        self._check_model_list_fields(expected_fields)

        # Open the edit layout form and check if all expected fields are visible
        self._open_edit_layout_form()
        self._check_field_cards(expected_fields)

        # The form dialog is still open. Let's change some fields, cancel, and check that the changes were not saved
        self._change_models(expected_fields)
        self.page.get_by_role("button", name="Cancel").click()
        self._open_edit_layout_form()
        self._check_field_cards(expected_fields)

        # The form dialog is still open. Let's change the fields again, save, and check that the changes were saved
        changed_fields = self._change_models(expected_fields)
        self.page.get_by_role("button", name="Save").click()
        time.sleep(self.sleep_interval)  # Wait for the page to reload
        expect(
            self.page.get_by_role("heading", name="Blog administration")
        ).to_be_visible()
        self._check_model_list_fields(changed_fields)
        self._open_edit_layout_form()
        self._check_field_cards(changed_fields)
        self.page.get_by_role("button", name="Cancel").click()

    def _check_app_list_fields(self, expected_fields: list[FieldCard]) -> None:
        # Let's check if all expected original models are visible and follow the correct order
        container = self.page.locator("#content-main")
        visible_fields = [field for field in expected_fields if field.visible]
        assert container.locator("caption").count() == len(visible_fields)

        for idx, expected_field in enumerate(visible_fields):
            caption = container.locator("caption").nth(idx)
            expect(caption).to_have_text(expected_field.description)

        # Check that the "Comments" model has been hidden
        expect(container.get_by_text("Comments")).not_to_be_visible()

    def _change_apps(self, original_fields: list[FieldCard]) -> list[FieldCard]:
        fields = self._toggle_field_card(original_fields, "Contact_Messages")
        # Let's drag the 3rd card to the top
        return self._drag_field_card(fields, 2, 0)

    def _test_admin_index(self, username: str) -> None:
        # Navigate to admin index page
        self._navigate_to("/admin/")
        expect(
            self.page.get_by_role("heading", name="Site administration")
        ).to_be_visible()

        expected_fields = [
            FieldCard("Blog", True),
            FieldCard("Contact_Messages", True),
            FieldCard("Users", True),
        ]

        if username == self.admin_username:
            expected_fields.insert(
                0, FieldCard("Authentication and Authorization", True)
            )

        self._check_app_list_fields(expected_fields)

        # Open the edit layout form and check if all expected fields are visible
        self._open_edit_layout_form()
        self._check_field_cards(expected_fields)

        # The form dialog is still open. Let's change some fields, cancel, and check that the changes were not saved
        self._change_apps(expected_fields)
        self.page.get_by_role("button", name="Cancel").click()
        self._open_edit_layout_form()
        self._check_field_cards(expected_fields)

        # The form dialog is still open. Let's change the fields again, save, and check that the changes were saved
        changed_fields = self._change_apps(expected_fields)
        self.page.get_by_role("button", name="Save").click()
        time.sleep(self.sleep_interval)  # Wait for the page to reload
        expect(
            self.page.get_by_role("heading", name="Site administration")
        ).to_be_visible()
        self._check_app_list_fields(changed_fields)
        self._open_edit_layout_form()
        self._check_field_cards(changed_fields)
        self.page.get_by_role("button", name="Cancel").click()

    def _test_user(self, username: str) -> None:
        self._login(username)
        self._test_users_change_list(username)
        self._test_blog_app_index(username)
        self._test_admin_index(username)

    def test_app(self) -> None:
        self._test_user(self.admin_username)
        self._logout()
        self._test_user(self.staff_username)
