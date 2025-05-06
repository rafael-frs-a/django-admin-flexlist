import json
import typing as t

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse
from django.views import View

from django_admin_flexlist import services


class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that ensures only staff users can access the view.
    """

    request: HttpRequest

    def test_func(self) -> bool:
        """
        Checks if the current user is authenticated and has staff privileges.

        Returns:
            True if the user is authenticated and is staff, False otherwise
        """
        return (
            self.request.user.is_authenticated
            and t.cast(User, self.request.user).is_staff
        )


class AppModelListDisplayView(StaffRequiredMixin, View):
    """
    View for managing the list display configuration of admin models.
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.service = services.AppModelListDisplayViewService()

    def get(
        self, request: HttpRequest, app_label: str, model_name: str
    ) -> JsonResponse:
        """
        Retrieves the list display configuration for a specific model.

        Args:
            request: The HTTP request object
            app_label: The Django app label
            model_name: The name of the model

        Returns:
            JSON response containing the list display configuration:
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

        list_display = self.service.get_list_fields(request, app_label, model_name)
        return JsonResponse({"data": list_display})

    def post(
        self, request: HttpRequest, app_label: str, model_name: str
    ) -> JsonResponse:
        """
        Updates the list display configuration for a specific model.

        Args:
            request: The HTTP request object
            app_label: The Django app label
            model_name: The name of the model

        Returns:
            JSON response containing the updated list display configuration:
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

        Raises:
            JsonResponse with status 400 if the request body contains invalid JSON
        """

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        list_display = self.service.update_list_fields(
            request, app_label, model_name, body["data"]
        )
        return JsonResponse({"data": list_display})


class AppListView(StaffRequiredMixin, View):
    """
    View for managing the admin app list configuration.
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.service = services.AppListViewService()

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Retrieves the the app list configuration for the admin interface.

        Args:
            request: The HTTP request object

        Returns:
            JSON response containing the app list configuration:
            {
                "data": [
                    {
                        "name": "app_name",
                        "visible": true,
                        "description": "App Description"
                    },
                    ...
                ]
            }
        """

        list_display = self.service.get_app_list(request)
        return JsonResponse({"data": list_display})

    def post(self, request: HttpRequest) -> JsonResponse:
        """
        Updates the app list configuration for the admin interface.

        Args:
            request: The HTTP request object

        Returns:
            JSON response containing the updated app list configuration:
            {
                "data": [
                    {
                        "name": "app_name",
                        "visible": true,
                        "description": "App Description"
                    },
                    ...
                ]
            }

        Raises:
            JsonResponse with status 400 if the request body contains invalid JSON
        """

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        list_display = self.service.update_app_list(request, body["data"])
        return JsonResponse({"data": list_display})


class AppModelListView(StaffRequiredMixin, View):
    """
    View for managing the admin model list configuration.
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self.service = services.AppModelListViewService()

    def get(self, request: HttpRequest, app_label: str) -> JsonResponse:
        """
        Retrieves the the model list configuration for the app.

        Args:
            request: The HTTP request object
            app_label: The Django app label

        Returns:
            JSON response containing the model list configuration:
            {
                "data": [
                    {
                        "name": "model_name",
                        "visible": true,
                        "description": "Model Description"
                    },
                    ...
                ]
            }
        """

        list_display = self.service.get_model_list(request, app_label)
        return JsonResponse({"data": list_display})

    def post(self, request: HttpRequest, app_label: str) -> JsonResponse:
        """
        Updates the model list configuration for the app.

        Args:
            request: The HTTP request object

        Returns:
            JSON response containing the updated model list configuration:
            {
                "data": [
                    {
                        "name": "model_name",
                        "visible": true,
                        "description": "Model Description"
                    },
                    ...
                ]
            }

        Raises:
            JsonResponse with status 400 if the request body contains invalid JSON
        """

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        list_display = self.service.update_model_list(request, app_label, body["data"])
        return JsonResponse({"data": list_display})
