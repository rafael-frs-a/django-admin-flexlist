import typing as t

from django.contrib.auth.models import AbstractBaseUser

from django_admin_flexlist import utils
from django_admin_flexlist.models import DjangoAdminFlexListConfig


class FlexListConfigStore(utils.Singleton):
    """
    Manages the storage and retrieval of flexlist configuration objects.
    """

    def get_or_create_config(self, user: AbstractBaseUser) -> DjangoAdminFlexListConfig:
        """
        Retrieves or creates a flexlist configuration for the given user.

        Args:
            user: The user to get or create the configuration for

        Returns:
            The user's flexlist configuration object
        """

        flexlist_config, _ = DjangoAdminFlexListConfig.objects.get_or_create(user=user)
        return flexlist_config

    def get_config_list_fields(
        self, flexlist_config: DjangoAdminFlexListConfig, path: list[str]
    ) -> list[utils.FlexListField]:
        """
        Retrieves a list of flexlist fields from the configuration at the specified path.

        Args:
            flexlist_config: The flexlist configuration object
            path: List of keys representing the path to the fields in the config

        Returns:
            A list of FlexListField objects found at the specified path
        """

        if not path:
            return []

        config = utils.get_dict_from_value(flexlist_config.config)

        for key in path[:-1]:
            config = utils.get_dict_from_value(config.get(key))

        # Last key in the path is expected to be a list of dictionaries.
        list_dict_fields = utils.get_list_from_value(config.get(path[-1]))
        result: list[utils.FlexListField] = []

        for field in list_dict_fields:
            try:
                result.append(utils.FlexListField(**field))
            except TypeError:
                continue

        return result

    def update_config(
        self, flexlist_config: DjangoAdminFlexListConfig, payload: dict[str, t.Any]
    ) -> DjangoAdminFlexListConfig:
        """
        Updates the flexlist configuration with new data.

        Args:
            flexlist_config: The flexlist configuration object to update
            payload: Dictionary containing the new configuration data

        Returns:
            The updated flexlist configuration object
        """

        utils.deep_update_dict(flexlist_config.config, payload)
        flexlist_config.save(update_fields=["config"])
        return flexlist_config
