import typing as t

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
    Acts as an intermediary between `FlexListAdmin` and `AppModelListDisplayService`.
    """

    def __init__(self) -> None:
        self.service = AppModelListDisplayService()

    def get_custom_list_display(
        self, request: HttpRequest, model: type[models.Model]
    ) -> list[str]:
        """
        Retrieves and returns a list of visible flexlist field names from the configuration.

        Args:
            request: The HTTP request object
            model: The Django model class

        Returns:
            A list of strings containing the names of visible fields
        """

        fields = self.service.get_list_fields(request, model)
        return [field.name for field in fields if field.visible]


class AppModelListDisplayViewService(utils.Singleton):
    """
    Acts as an intermediary between `AppModelListDisplayView` and `AppModelListDisplayService`.
    """

    def __init__(self) -> None:
        self.service = AppModelListDisplayService()
        self.store = FlexListConfigStore()

    def get_list_fields(
        self, request: HttpRequest, app_label: str, model_name: str
    ) -> list[dict[str, str | bool]]:
        """
        Retrieves and returns the list of fields for a specific model.

        Args:
            request: The HTTP request object
            app_label: The Django app label
            model_name: The name of the model

        Returns:
            A list of dictionaries containing field information
        """

        model = self.get_model(app_label, model_name)

        if model is None:
            return []

        fields = self.service.get_list_fields(request, model)
        return utils.make_payload_from_list_fields(fields)

    def get_model(
        self, app_label: str, model_name: str
    ) -> t.Optional[type[models.Model]]:
        """
        Retrieves a model class using the provided app label and model name.

        Args:
            app_label: The Django app label
            model_name: The name of the model

        Returns:
            The model class if found, None otherwise
        """

        return apps.get_model(app_label, model_name)

    def update_list_fields(
        self, request: HttpRequest, app_label: str, model_name: str, data: t.Any
    ) -> list[dict[str, str | bool]]:
        """
        Updates the list fields configuration for a specific model.

        Args:
            request: The HTTP request object
            app_label: The Django app label
            model_name: The name of the model
            data: The new field configuration data

        Returns:
            A list of dictionaries containing the updated field information
        """

        model = self.get_model(app_label, model_name)

        if model is None:
            return []

        list_fields = utils.make_list_fields_from_data(data)
        updated_list_fields = self.service.update_list_fields(
            request, model, list_fields
        )

        return utils.make_payload_from_list_fields(updated_list_fields)


class AppModelListDisplayService(utils.Singleton):
    """
    Implements the core logic for managing custom list display fields.
    """

    def __init__(self) -> None:
        self.store = FlexListConfigStore()

    def get_list_fields(
        self, request: HttpRequest, model: type[models.Model]
    ) -> list[utils.FlexListField]:
        """
        Retrieves the list of fields from the flexlist configuration.

        Args:
            request: The HTTP request object
            model: The Django model class

        Returns:
            A list of FlexListField objects
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
        Processes and combines fields from both the flexlist config and original list display.

        Args:
            request: The HTTP request object
            model: The Django model class
            flexlist_config: The current flexlist configuration

        Returns:
            A list of FlexListField objects combining both config and original fields
        """

        path = self._make_list_display_path(model)
        fields = self.store.get_config_list_fields(flexlist_config, path)

        # Use original list display as source of truth
        original_list_display_fields = self.get_original_list_display_fields(
            request, model
        )

        result: list[utils.FlexListField] = []
        seen_fields: set[str] = set()

        # Add to the result the fields from the flexlist config that are present in the original list display
        for field in fields:
            if field.name not in original_list_display_fields:
                continue

            # Let's prioritize the description from the original field
            field.description = original_list_display_fields[field.name]
            result.append(field)
            seen_fields.add(field.name)

        # Add to the result the fields from the original list display that are not present in the flexlist config
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
        Creates a path to the flexlist config's list fields.

        Args:
            model: The Django model class

        Returns:
            A list of strings representing the path to the list fields configuration
        """

        app_label = model._meta.app_label.lower()
        model_name = str(model._meta.model_name).lower()
        return ["apps", app_label, "models", model_name, "list_display"]

    def get_original_list_display_fields(
        self, request: HttpRequest, model: type[models.Model]
    ) -> dict[str, str]:
        """
        Retrieves the original list display fields and their descriptions.

        Args:
            request: The HTTP request object
            model: The Django model class

        Returns:
            A dictionary mapping field names to their descriptions
        """

        model_admin = self.get_model_admin(model)

        if not hasattr(model_admin, "_daf_original_get_list_display"):
            return {}

        # Make sure to call `_daf_original_get_list_display` over `get_list_display` to avoid infinite loops
        original_list_display = model_admin._daf_original_get_list_display(request)
        list_display = self.cast_list_display_to_list_of_strings(original_list_display)
        fields_descriptions = {
            field: self.get_field_description(field, model, model_admin)
            for field in list_display
        }
        return fields_descriptions

    def get_model_admin(self, model: type[models.Model]) -> admin.ModelAdmin:  # type: ignore[type-arg]
        """
        Retrieves the admin class for a given model.

        Args:
            model: The Django model class

        Returns:
            The ModelAdmin class for the given model

        Raises:
            ValueError: If no admin class is found for the model
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
        Converts a list or tuple of fields to a list of string field names.

        Args:
            list_display: A list or tuple of field references

        Returns:
            A list of string field names
        """

        return [self.get_field_name(field) for field in list_display]

    def get_field_name(self, field: t.Any) -> str:
        """
        Extracts the name of a field from various field types.

        Args:
            field: A field reference (callable or string)

        Returns:
            The string name of the field
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
        Determines the description for a field using multiple fallback methods:
        1. Django string representation
        2. Custom admin field with short description
        3. Field's verbose name
        4. Field name in title case

        Args:
            field: The field name
            model: The Django model class
            model_admin: The model's admin class

        Returns:
            The field description as a string
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
        Updates the user's flexlist configuration with new field settings.

        Args:
            request: The HTTP request object
            model: The Django model class
            list_fields: The new list of FlexListField objects

        Returns:
            The updated list of FlexListField objects
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = self.store.get_or_create_config(request.user)
        path = self._make_list_display_path(model)
        payload = utils.make_update_payload_from_list_fields(list_fields, path)
        flexlist_config = self.store.update_config(flexlist_config, payload)
        return self._get_list_fields(request, model, flexlist_config)
