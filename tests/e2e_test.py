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

    def _toggle_field_card(
        self, fields: list[FieldCard], field_description: str
    ) -> list[FieldCard]:
        fields_copy = [FieldCard(field.description, field.visible) for field in fields]
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

    def _change_fields(self, original_fields: list[FieldCard]) -> list[FieldCard]:
        fields: list[FieldCard] = []
        fields = self._toggle_field_card(original_fields, "First name")
        fields = self._toggle_field_card(fields, "Last name")

        # Let's drag the 3rd card to the top
        source_field_card = fields[2]
        target_field_card = fields[0]
        fields = fields[2:3] + fields[:2] + fields[3:]
        source = self._get_field_card(source_field_card.description)
        target = self._get_field_card(target_field_card.description)
        source.drag_to(target)

        return fields

    def _check_list_view_fields(self, expected_fields: list[FieldCard]) -> None:
        # Let's check if all expected original fields are visible and follow the correct order
        thead = self.page.locator("#result_list thead")
        skip = 1  # Skip the checkbox column
        visible_fields = [field for field in expected_fields if field.visible]
        assert thead.locator("th").count() == len(visible_fields) + skip

        for idx, expected_field in enumerate(visible_fields, start=skip):
            th = thead.locator("th").nth(idx)
            expect(th).to_have_text(expected_field.description)

    def _test_user(self, username: str) -> None:
        self._login(username)

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
        time.sleep(1)  # Wait for the page to reload
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

    def test_app(self) -> None:
        self._test_user(self.admin_username)
        self._logout()
        self._test_user(self.staff_username)
