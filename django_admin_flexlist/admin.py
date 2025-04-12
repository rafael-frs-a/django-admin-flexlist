from django.contrib import admin
from django.http import HttpRequest


class FlexListAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """
    This class is used to intercept the `get_list_display` method from its subclasses
    and apply the `list_display` configuration from the `DjangoAdminFlexListConfig` model.
    It also adds an option to change the list display by adding a button to the change list page.
    """

    change_list_template = "django_admin_flexlist/change_list.html"

    @classmethod
    def __init_subclass__(cls) -> None:
        from django_admin_flexlist.services import FlexListService

        super().__init_subclass__()
        flexlist_service = FlexListService()
        original_get_list_display = cls.get_list_display

        def wrapped(self: admin.ModelAdmin, request: HttpRequest) -> list[str]:  # type: ignore[type-arg]
            return flexlist_service.get_list_display(request, self.model)

        cls._daf_original_get_list_display = original_get_list_display  # type: ignore[attr-defined]
        cls.get_list_display = wrapped  # type: ignore[assignment]
