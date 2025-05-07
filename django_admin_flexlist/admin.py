import typing as t

from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.http import HttpRequest


class FlexListAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """
    This class intercepts the `get_list_display` method to apply custom list display
    configurations from the `DjangoAdminFlexListConfig` model. It adds a button to
    the change list page that allows users to customize the list display.
    """

    change_list_template = "django_admin_flexlist/change_list.html"

    @classmethod
    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        """
        Initializes subclasses by wrapping the `get_list_display` method to use
        custom list display configurations.
        """
        from django_admin_flexlist.services import FlexListAdminService

        super().__init_subclass__(**kwargs)
        service = FlexListAdminService()
        original_get_list_display = cls.get_list_display

        def wrapped(
            self: admin.ModelAdmin,  # type: ignore[type-arg]
            request: HttpRequest,
        ) -> list[str]:
            # Prevent infinite loops
            if getattr(self, "_daf_skip_custom_list_display", False):
                return original_get_list_display(self, request)  # type: ignore[return-value]

            self._daf_skip_custom_list_display = True  # type: ignore[attr-defined]

            try:
                return service.get_custom_list_display(request, self.model)
            finally:
                self._daf_skip_custom_list_display = False  # type: ignore[attr-defined]

        cls._daf_original_get_list_display = original_get_list_display  # type: ignore[attr-defined]
        cls.get_list_display = wrapped  # type: ignore[assignment]


class FlexListAdminSite(admin.AdminSite):
    """
    This class adds an "Edit layout" button to the admin pages and implements
    functionality to customize the order and visibility of admin apps, similar to
    the list display customization in `FlexListAdmin`.
    """

    index_template = "django_admin_flexlist/index.html"
    app_index_template = "django_admin_flexlist/app_index.html"

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super().__init__(*args, **kwargs)
        self._daf_original_get_app_list = super().get_app_list

    def get_app_list(
        self, request: HttpRequest, app_label: t.Optional[str] = None
    ) -> list[dict[str, t.Any]]:
        from django_admin_flexlist.services import FlexListAdminSiteService

        # Prevent infinite loops
        if getattr(self, "_daf_skip_custom_app_list", False):
            return super().get_app_list(request, app_label)

        try:
            self._daf_skip_custom_app_list = True
            service = FlexListAdminSiteService()
            return service.get_custom_app_list(request, app_label)
        finally:
            self._daf_skip_custom_app_list = False


class FlexListAdminConfig(AdminConfig):
    """
    Admin configuration class that sets `FlexListAdminSite` as the default admin site.
    """

    default_site = "django_admin_flexlist.FlexListAdminSite"
