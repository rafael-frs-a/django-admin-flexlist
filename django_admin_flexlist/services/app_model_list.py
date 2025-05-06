import typing as t

from django.contrib import admin
from django.http import HttpRequest

from django_admin_flexlist import utils
from django_admin_flexlist.models import DjangoAdminFlexListConfig
from django_admin_flexlist.stores import FlexListConfigStore


class FlexListAdminSiteService(utils.Singleton):
    """
    Retrieves both app list and model list fields from the flexlist config to be used by `FlexListAdminSite`.
    """

    def __init__(self) -> None:
        self.service = AppModelListService()
        self.store = FlexListConfigStore()

    def get_custom_app_list(
        self, request: HttpRequest, app_label: t.Optional[str] = None
    ) -> list[dict[str, t.Any]]:
        """
        Retrieves and returns a customized app list based on the flexlist configuration.

        Args:
            request: The HTTP request object
            app_label: Optional app label to filter the app list

        Returns:
            A list of dictionaries containing app information
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = self.store.get_or_create_config(request.user)
        app_list_path = self.service.make_app_list_path()
        app_list_fields = self.store.get_config_list_fields(
            flexlist_config, app_list_path
        )

        # Use original app list as source of truth
        original_app_list = self.service.get_original_app_list(request, app_label)
        original_app_list_lookup = {app["app_label"]: app for app in original_app_list}

        result: list[dict[str, t.Any]] = []
        seen_app_labels: set[str] = set()

        # Add to the result the fields from the flexlist config that are present in the original app list
        for app_field in app_list_fields:
            if app_field.name not in original_app_list_lookup:
                continue

            seen_app_labels.add(app_field.name)

            if not app_field.visible:
                continue

            result.append(original_app_list_lookup[app_field.name])

        # Add to the result the fields from the original app list that are not present in the flexlist config
        for app_label, app in original_app_list_lookup.items():
            if app_label in seen_app_labels:
                continue

            result.append(app)

        for app in result:
            model_list_path = self.service.make_model_list_path(app["app_label"])
            model_list_fields = self.store.get_config_list_fields(
                flexlist_config, model_list_path
            )
            original_model_list_lookup = {
                model["object_name"]: model for model in app["models"]
            }

            models_result: list[dict[str, t.Any]] = []
            seen_model_names: set[str] = set()

            # Add to the result the fields from the flexlist config that are present in the original model list
            for model_field in model_list_fields:
                if model_field.name not in original_model_list_lookup:
                    continue

                seen_model_names.add(model_field.name)

                if not model_field.visible:
                    continue

                models_result.append(original_model_list_lookup[model_field.name])

            # Add to the result the fields from the original model list that are not present in the flexlist config
            for model_name, model in original_model_list_lookup.items():
                if model_name in seen_model_names:
                    continue

                models_result.append(model)

            app["models"] = models_result

        return result


class AppModelListService(utils.Singleton):
    """
    Implements common logic between the admin side and the views.
    """

    def make_app_list_path(self) -> list[str]:
        """
        Creates a path to the flexlist config's app list fields.

        Returns:
            A list of strings representing the path to the app list configuration
        """
        return ["app_list"]

    def make_model_list_path(self, app_label: str) -> list[str]:
        """
        Creates a path to the flexlist config's model list fields.

        Args:
            app_label: The Django app label

        Returns:
            A list of strings representing the path to the model list configuration
        """
        return ["apps", app_label, "model_list"]

    def get_original_app_list(
        self, request: HttpRequest, app_label: t.Optional[str] = None
    ) -> list[dict[str, t.Any]]:
        """
        Retrieves the original app list from Django's admin site.

        Args:
            request: The HTTP request object
            app_label: Optional app label to filter the app list

        Returns:
            A list of dictionaries containing app information
        """

        if not request.user.is_authenticated:
            return []

        admin_site = admin.site

        if not hasattr(admin_site, "_daf_original_get_app_list"):
            return []

        app_list = admin_site._daf_original_get_app_list(request, app_label)
        typed_app_list = t.cast(list[dict[str, t.Any]], app_list)
        return typed_app_list


class AppListViewService(utils.Singleton):
    """
    Retrieves and updates the app list fields for `AppListView`
    """

    def __init__(self) -> None:
        self.service = AppModelListService()
        self.store = FlexListConfigStore()

    def get_app_list(
        self,
        request: HttpRequest,
        flexlist_config: t.Optional[DjangoAdminFlexListConfig] = None,
    ) -> list[dict[str, str | bool]]:
        """
        Retrieves and returns the list of apps with their visibility settings.

        Args:
            request: The HTTP request object
            flexlist_config: Optional flexlist configuration to use

        Returns:
            A list of dictionaries containing app information and visibility settings
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = flexlist_config or self.store.get_or_create_config(
            request.user
        )
        app_list_path = self.service.make_app_list_path()
        app_list_fields = self.store.get_config_list_fields(
            flexlist_config, app_list_path
        )

        # Use original app list as source of truth
        original_app_list = self.service.get_original_app_list(request)
        original_app_list_lookup = {app["app_label"]: app for app in original_app_list}

        result_list_fields: list[utils.FlexListField] = []
        seen_app_labels: set[str] = set()

        # Add to the result the fields from the flexlist config that are present in the original app list
        for app_field in app_list_fields:
            if app_field.name not in original_app_list_lookup:
                continue

            # Let's prioritize the description from the original app list
            app_field.description = original_app_list_lookup[app_field.name]["name"]
            result_list_fields.append(app_field)
            seen_app_labels.add(app_field.name)

        # Add to the result the fields from the original app list that are not present in the flexlist config
        for app_label, app in original_app_list_lookup.items():
            if app_label in seen_app_labels:
                continue

            result_list_fields.append(
                utils.FlexListField(
                    name=app["app_label"], description=app["name"], visible=True
                )
            )

        return utils.make_payload_from_list_fields(result_list_fields)

    def update_app_list(
        self, request: HttpRequest, data: t.Any
    ) -> list[dict[str, str | bool]]:
        """
        Updates the app list configuration.

        Args:
            request: The HTTP request object
            data: The new app list configuration data

        Returns:
            A list of dictionaries containing the updated app information
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = self.store.get_or_create_config(request.user)
        path = self.service.make_app_list_path()
        list_fields = utils.make_list_fields_from_data(data)
        payload = utils.make_update_payload_from_list_fields(list_fields, path)
        flexlist_config = self.store.update_config(flexlist_config, payload)
        return self.get_app_list(request, flexlist_config)


class AppModelListViewService(utils.Singleton):
    """
    Retrieves and updates the model list fields for `AppModelListView`
    """

    def __init__(self) -> None:
        self.service = AppModelListService()
        self.store = FlexListConfigStore()

    def get_model_list(
        self,
        request: HttpRequest,
        app_label: str,
        flexlist_config: t.Optional[DjangoAdminFlexListConfig] = None,
    ) -> list[dict[str, str | bool]]:
        """
        Retrieves and returns the list of models for a specific app with their visibility settings.

        Args:
            request: The HTTP request object
            app_label: The Django app label
            flexlist_config: Optional flexlist configuration to use

        Returns:
            A list of dictionaries containing model information and visibility settings
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = flexlist_config or self.store.get_or_create_config(
            request.user
        )
        model_list_path = self.service.make_model_list_path(app_label)
        model_list_fields = self.store.get_config_list_fields(
            flexlist_config, model_list_path
        )

        # Use original app list as source of truth
        original_app_list = self.service.get_original_app_list(request, app_label)

        if not original_app_list:
            return []

        original_app = original_app_list[0]
        original_model_list_lookup = {
            model["object_name"]: model for model in original_app["models"]
        }

        result_list_fields: list[utils.FlexListField] = []
        seen_model_names: set[str] = set()

        # Add to the result the fields from the flexlist config that are present in the original model list
        for model_field in model_list_fields:
            if model_field.name not in original_model_list_lookup:
                continue

            # Let's prioritize the description from the original model list
            model_field.description = original_model_list_lookup[model_field.name][
                "name"
            ]
            result_list_fields.append(model_field)
            seen_model_names.add(model_field.name)

        # Add to the result the fields from the original model list that are not present in the flexlist config
        for model_label, model in original_model_list_lookup.items():
            if model_label in seen_model_names:
                continue

            result_list_fields.append(
                utils.FlexListField(
                    name=model["object_name"], description=model["name"], visible=True
                )
            )

        return utils.make_payload_from_list_fields(result_list_fields)

    def update_model_list(
        self, request: HttpRequest, app_label: str, data: t.Any
    ) -> list[dict[str, str | bool]]:
        """
        Updates the model list configuration for a specific app.

        Args:
            request: The HTTP request object
            app_label: The Django app label
            data: The new model list configuration data

        Returns:
            A list of dictionaries containing the updated model information
        """

        if not request.user.is_authenticated:
            return []

        flexlist_config = self.store.get_or_create_config(request.user)
        path = self.service.make_model_list_path(app_label)
        list_fields = utils.make_list_fields_from_data(data)
        payload = utils.make_update_payload_from_list_fields(list_fields, path)
        flexlist_config = self.store.update_config(flexlist_config, payload)
        return self.get_model_list(request, app_label, flexlist_config)
