import typing as t

from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import HttpRequest

from django_admin_flexlist.models import DjangoAdminFlexListConfig


class FlexListService:
    """
    This class implements the logic to read and write `DjangoAdminFlexListConfig` objects.
    """

    def get_list_display(
        self, request: HttpRequest, model: type[models.Model]
    ) -> list[str]:
        """
        Get the config's `list_display` and return a list of fields that should be visible.
        """
        model_list_display = self.get_model_list_display(request, model)
        return [
            t.cast(str, field["name"])
            for field in model_list_display
            if field["visible"]
        ]

    def get_model_list_display(
        self,
        request: HttpRequest,
        model: type[models.Model],
        flexlist_config: t.Optional[DjangoAdminFlexListConfig] = None,
    ) -> list[dict[str, str | bool]]:
        """
        1. Get the user's flexlist config.
        2. Get the model's original list display to use as source of truth.
        3. Get the config's list display for the model.
        4. Remove from the config's list display the fields that are not in the model's original list display.
        5. Add to the config's list display the fields that are in the model's original list display but not in the config's list display.
        6. Return the updated list display.
        Example of expected return format:
        [
            {
                "name": "field_name",
                "description": "Field Description",
                "visible": True
            }
        ]
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = flexlist_config or self.get_or_create_config(request.user)
        original_list_display = self.get_original_list_display(request, model)
        config_list_display = self.get_config_list_display(flexlist_config, model)
        adjusted_config_list_display: list[dict[str, str | bool]] = []
        seen_fields: set[str] = set()

        for field in config_list_display:
            if field["name"] in original_list_display:
                adjusted_config_list_display.append(field)
                seen_fields.add(field["name"])

        for field_name, description in original_list_display.items():
            if field_name in seen_fields:
                continue

            adjusted_config_list_display.append(
                {"name": field_name, "description": description, "visible": True}
            )

        return adjusted_config_list_display

    def get_or_create_config(self, user: AbstractBaseUser) -> DjangoAdminFlexListConfig:
        """
        Get the user's flexlist config or create a new one if it doesn't exist.
        """
        flexlist_config, _ = DjangoAdminFlexListConfig.objects.get_or_create(user=user)
        return flexlist_config

    def get_original_list_display(
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
        model_admin = self.locate_model_admin(model)

        if not hasattr(model_admin, "_daf_original_get_list_display"):
            return {}

        original_list_display = model_admin._daf_original_get_list_display(request)
        list_display = self.cast_list_display_to_list_of_strings(original_list_display)
        fields_descriptions = {
            field: self.get_field_description(field, model, model_admin)
            for field in list_display
        }
        return fields_descriptions

    def locate_model_admin(self, model: type[models.Model]) -> admin.ModelAdmin:  # type: ignore[type-arg]
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

    def get_model_list_display_from_names(
        self, request: HttpRequest, app_label: str, model_name: str
    ) -> list[dict[str, str | bool]]:
        """
        1. Get model from app label and model name.
        2. Return the model's original list display.
        """
        model = apps.get_model(app_label, model_name)

        if model is None:
            return []

        return self.get_model_list_display(request, model)

    def update_model_list_display(
        self,
        request: HttpRequest,
        app_label: str,
        model_name: str,
        list_display: list[dict[str, str | bool]],
    ) -> list[dict[str, str | bool]]:
        """
        1. Get the user's flexlist config.
        2. Get the model class from the app label and model name.
        3. Build a payload with the part of the config that should be updated.
        4. Deep update the config with the payload.
        5. Save the config.
        6. Return the updated model's list display.s
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = self.get_or_create_config(request.user)
        model = apps.get_model(app_label, model_name)

        if model is None:
            return []

        payload = {
            "apps": {
                app_label.lower(): {
                    "models": {
                        model_name.lower(): {
                            "list_display": list_display,
                        }
                    }
                }
            }
        }

        self.deep_update_dict(flexlist_config.config, payload)
        flexlist_config.save(update_fields=["config"])
        # Let's avoid another DB query to get the updated list display.
        return self.get_model_list_display(request, model, flexlist_config)

    def get_config_list_display(
        self, flexlist_config: DjangoAdminFlexListConfig, model: type[models.Model]
    ) -> list[dict[str, t.Any]]:
        """
        Get the corresponding model's list display from the flexlist config.
        JSON format is expected to follow the schema defined under the `schemas` directory.
        To ensure that format, let's use default values for each unexpected key.
        """
        config = flexlist_config.config

        if not isinstance(config, dict):
            config = {}

        app_label = model._meta.app_label.lower()
        model_name = str(model._meta.model_name).lower()

        if not isinstance(config.get("apps"), dict):
            config["apps"] = {}

        app_config = config["apps"].get(app_label)

        if not isinstance(app_config, dict):
            app_config = {}

        if not isinstance(app_config.get("models"), dict):
            app_config["models"] = {}

        model_config = app_config["models"].get(model_name)

        if not isinstance(model_config, dict):
            model_config = {}

        if not isinstance(model_config.get("list_display"), list):
            model_config["list_display"] = []

        list_display: list[dict[str, str | bool]] = []

        for field in model_config["list_display"]:
            if not isinstance(field, dict):
                continue

            if not isinstance(field.get("name"), str):
                continue

            if not isinstance(field.get("description"), str):
                continue

            if not isinstance(field.get("visible"), bool):
                continue

            list_display.append(
                {
                    "name": field["name"],
                    "description": field["description"],
                    "visible": field["visible"],
                }
            )

        return list_display

    def deep_update_dict(
        self,
        d1: dict[str, t.Any],
        d2: dict[str, t.Any],
        seen: t.Optional[set[int]] = None,
    ) -> None:
        """
        Update d1 with d2 recursively so we don't overwrite an entire item at the root,
        like the 'apps' key, when updating just one particular nested dictionary value.
        """

        if seen is None:
            seen = set()

        if id(d1) in seen:  # Prevent infinite loops with self-referencing dictionaries.
            return

        seen.add(id(d1))

        for key, value in d2.items():
            if isinstance(value, dict) and key in d1 and isinstance(d1[key], dict):
                self.deep_update_dict(d1[key], value, seen)
            else:
                d1[key] = value
