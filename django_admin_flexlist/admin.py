from django.contrib import admin
from django.http import HttpRequest

from django_admin_flexlist.services import FlexListService


class FlexListAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """
    This class is used to intercept the `get_list_display` method from its subclasses
    and apply the `list_display` configuration from the `DjangoAdminFlexListConfig` model.
    """

    flexlist_service = FlexListService()

    @classmethod
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        original_get_list_display = cls.get_list_display

        def wrapped(self: admin.ModelAdmin, request: HttpRequest) -> list[str]:  # type: ignore[type-arg]
            return cls.flexlist_service.get_list_display(request, self.model)

        cls._daf_original_get_list_display = original_get_list_display  # type: ignore[attr-defined]
        cls.get_list_display = wrapped  # type: ignore[assignment]
