import typing as t
from dataclasses import asdict

from django.apps import apps
from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import HttpRequest

from django_admin_flexlist import utils
from django_admin_flexlist.models import DjangoAdminFlexListConfig
from django_admin_flexlist.stores import FlexListConfigStore


class FlexListAdminService(utils.Singleton):
    """
    This class acts as an intermediary between `FlexListAdmin` and `AppModelListDisplayService`
    """

    def __init__(self) -> None:
        self.service = AppModelListDisplayService()

    def get_custom_list_display(
        self, request: HttpRequest, model: type[models.Model]
    ) -> list[str]:
        """
        1. Get list of flexlist fields from the config.
        2. Return a list of strings with the field names.
        """

        fields = self.service.get_list_fields(request, model)
        return [field.name for field in fields if field.visible]


class AppModelListDisplayViewService(utils.Singleton):
    """
    This class acts as an intermediary between `AppModelListDisplayView` and `AppModelListDisplayService`.
    """

    def __init__(self) -> None:
        self.service = AppModelListDisplayService()
        self.store = FlexListConfigStore()

    def get_list_fields(
        self, request: HttpRequest, app_label: str, model_name: str
    ) -> list[dict[str, str | bool]]:
        """
        1. Get the model class from the app label and model name.
        2. Get flexlist fields from the user's config.
        3. Convert list of `FlexListField` to list of dicts.
        """

        model = self.get_model(app_label, model_name)

        if model is None:
            return []

        fields = self.service.get_list_fields(request, model)
        return [asdict(field) for field in fields]

    def get_model(
        self, app_label: str, model_name: str
    ) -> t.Optional[type[models.Model]]:
        """
        Get a model from the given app label and model name.
        """

        return apps.get_model(app_label, model_name)

    def update_list_fields(
        self, request: HttpRequest, app_label: str, model_name: str, payload: t.Any
    ) -> list[dict[str, str | bool]]:
        """
        1. Get the model class from the app label and model name.
        2. Make list of `FlexListField` from the payload.
        3. Update the user's flexlist config with the new list of fields.
        4. Make a list of dicts from the updated list of fields.
        """

        model = self.get_model(app_label, model_name)

        if model is None:
            return []

        list_fields: list[utils.FlexListField] = []
        payload_list = utils.get_list_from_value(payload)

        for field in payload_list:
            field_dict = utils.get_dict_from_value(field)

            try:
                list_fields.append(utils.FlexListField(**field_dict))
            except TypeError:
                continue

        updated_list_fields = self.service.update_list_fields(
            request, model, list_fields
        )

        return [asdict(field) for field in updated_list_fields]


class AppModelListDisplayService(utils.Singleton):
    """
    This class implements the main logic over custom list display fields.
    """

    def __init__(self) -> None:
        self.store = FlexListConfigStore()

    def get_list_fields(
        self, request: HttpRequest, model: type[models.Model]
    ) -> list[utils.FlexListField]:
        """
        1. Get the flexlist config.
        2. Return the list of fields from the flexlist config.
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = self.store.get_or_create_config(request.user)
        return self._get_list_fields(request, model, flexlist_config)

    def _get_list_fields(
        self,
        request: HttpRequest,
        model: type[models.Model],
        flexlist_config: DjangoAdminFlexListConfig,
    ) -> list[utils.FlexListField]:
        """
        1. Make a path to the flexlist config's list fields.
        2. Get the flexlist config's list fields.
        3. Get original list display fields as the source of truth.
        4. Add to result the fields from the flexlist config that are in the original list display.
        5. Add to result the fields from the original list display that are not in the flexlist config.
        """

        path = self._make_list_display_path(model)
        fields = self.store.get_config_list_fields(flexlist_config, path)

        original_list_display_fields = self.get_original_list_display_fields(
            request, model
        )

        result: list[utils.FlexListField] = []
        seen_fields: set[str] = set()

        for field in fields:
            if field.name in original_list_display_fields:
                # Let's prioritize the description from the original field
                field.description = original_list_display_fields[field.name]
                result.append(field)
                seen_fields.add(field.name)

        for field_name, description in original_list_display_fields.items():
            if field_name in seen_fields:
                continue

            result.append(
                utils.FlexListField(
                    name=field_name, description=description, visible=True
                )
            )

        return result

    def _make_list_display_path(self, model: type[models.Model]) -> list[str]:
        """
        Make a path to the flexlist config's list fields.
        """

        app_label = model._meta.app_label.lower()
        model_name = str(model._meta.model_name).lower()
        return ["apps", app_label, "models", model_name, "list_display"]

    def get_original_list_display_fields(
        self, request: HttpRequest, model: type[models.Model]
    ) -> dict[str, str]:
        """
        1. Locate the model's admin class.
        2. Use its `_daf_original_get_list_display` method to get the original `list_display`, avoiding an infinite loop.
        3. Make sure `list_display` is a list of strings, as it must be serializable to JSON.
        4. Infer the field description for each field in the `list_display`.
        5. Return a dictionary, where each key is the field name and the value is the field description.
        Python 3.7+ should preserve the order of the keys.
        """

        model_admin = self.get_model_admin(model)

        if not hasattr(model_admin, "_daf_original_get_list_display"):
            return {}

        original_list_display = model_admin._daf_original_get_list_display(request)
        list_display = self.cast_list_display_to_list_of_strings(original_list_display)
        fields_descriptions = {
            field: self.get_field_description(field, model, model_admin)
            for field in list_display
        }
        return fields_descriptions

    def get_model_admin(self, model: type[models.Model]) -> admin.ModelAdmin:  # type: ignore[type-arg]
        """
        Locate the admin class for a given model.
        """

        admin_site = admin.site
        model_admin = admin_site._registry[model]

        if model_admin is None:
            raise ValueError(f"No admin class found for model {model}")

        return model_admin

    def cast_list_display_to_list_of_strings(
        self, list_display: list[t.Any] | tuple[t.Any, ...]
    ) -> list[str]:
        """
        Cast a list or tuple of fields to a list of strings.
        """

        return [self.get_field_name(field) for field in list_display]

    def get_field_name(self, field: t.Any) -> str:
        """
        Get the name of a field.
        If it's a callable, return the name of the function. Otherwise, return the name of the field.
        """

        if hasattr(field, "__name__"):
            return str(field.__name__)

        if hasattr(field, "__func__"):
            return str(field.__func__.__name__)

        return str(field)

    def get_field_description(
        self,
        field: str,
        model: type[models.Model],
        model_admin: admin.ModelAdmin,  # type: ignore[type-arg]
    ) -> str:
        """
        Infer the description of a field.
        1. Check for Django string representation.
        2. Check if it's a custom admin field with short description informed.
        3. Check for the field's verbose name.
        4. Fallback to the field name in title case.
        """

        default_description = field.replace("_", " ").strip().title()

        if field == "__str__":
            if model._meta.verbose_name is not None:
                return str(model._meta.verbose_name).strip().title()

        if hasattr(model_admin, field):
            attr = getattr(model_admin, field)

            if callable(attr):
                return (
                    getattr(attr, "short_description", default_description)
                    .strip()
                    .title()
                )

        try:
            model_field = model._meta.get_field(field)

            if hasattr(model_field, "verbose_name"):
                return model_field.verbose_name.strip().title()

            return default_description
        except FieldDoesNotExist:
            return default_description

    def update_list_fields(
        self,
        request: HttpRequest,
        model: type[models.Model],
        list_fields: list[utils.FlexListField],
    ) -> list[utils.FlexListField]:
        """
        1. Get the user's flexlist config.
        2. Build a payload with the part of the config that should be updated.
        3. Update the config with the payload.
        4. Return the updated list fields.
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = self.store.get_or_create_config(request.user)
        payload = self._make_update_payload(model, list_fields)
        flexlist_config = self.store.update_config(flexlist_config, payload)
        return self._get_list_fields(request, model, flexlist_config)

    def _make_update_payload(
        self, model: type[models.Model], list_fields: list[utils.FlexListField]
    ) -> dict[str, t.Any]:
        """
        1. Make a path to the flexlist config's list fields.
        2. Add empty dicts for each key in the path, except for the last one.
        3. Make the last key a list of dictionaries, each representing a `FlexListField`.
        """

        path = self._make_list_display_path(model)

        payload: dict[str, t.Any] = {}
        current: dict[str, t.Any] = payload

        for key in path[:-1]:
            current[key] = {}
            current = current[key]

        current[path[-1]] = [asdict(field) for field in list_fields]
        return payload
