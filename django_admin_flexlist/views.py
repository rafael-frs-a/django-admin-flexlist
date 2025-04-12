import json
import typing as t

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse
from django.views import View

from django_admin_flexlist.services import FlexListService


class StaffRequiredMixin(UserPassesTestMixin):
    request: HttpRequest

    def test_func(self) -> bool:
        return (
            self.request.user.is_authenticated
            and t.cast(User, self.request.user).is_staff
        )


class AppModelListDisplayView(StaffRequiredMixin, View):
    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.flexlist_service = FlexListService()

    def get(
        self, request: HttpRequest, app_label: str, model_name: str
    ) -> JsonResponse:
        """
        Expected response format:
        {
            "data": [
                {
                    "name": "field_name",
                    "visible": true,
                    "description": "Field Description"
                },
                ...
            ]
        }
        """
        list_display = self.flexlist_service.get_model_list_display_from_names(
            request, app_label, model_name
        )
        return JsonResponse({"data": list_display})

    def post(
        self, request: HttpRequest, app_label: str, model_name: str
    ) -> JsonResponse:
        """
        Expected request format:
        {
            "data": [
                {
                    "name": "field_name",
                    "visible": true,
                    "description": "Field Description"
                },
                ...
            ]
        }
        Expected response format: same as the expected request format.
        """
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        list_display = self.flexlist_service.update_model_list_display(
            request, app_label, model_name, body["data"]
        )
        return JsonResponse({"data": list_display})
