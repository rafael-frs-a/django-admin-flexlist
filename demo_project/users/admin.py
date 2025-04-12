import typing as t

from django.contrib import admin
from django.http import HttpRequest
from users.models import User

from django_admin_flexlist import FlexListAdmin


@admin.register(User)
class UserAdmin(FlexListAdmin):
    # We can either use the `list_display` attribute or the `get_list_display` method.
    list_display = (
        "username",
        "full_name",
        "email",
        "formatted_dob",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )

    def get_list_display(self, request: HttpRequest) -> tuple[str, ...]:
        # If the user is superuser, let's add `last_login` to the list display.
        user = t.cast(User, request.user)

        if user.is_authenticated and user.is_superuser:
            return self.list_display + ("last_login",)

        return self.list_display

    @admin.display(description="DOB")
    def formatted_dob(self, obj: User) -> str:
        return obj.dob.strftime("%Y-%m-%d") if obj.dob else "-"
