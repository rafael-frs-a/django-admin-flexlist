import typing as t

from django.contrib.auth.models import AbstractBaseUser

from django_admin_flexlist import utils
from django_admin_flexlist.models import DjangoAdminFlexListConfig


class FlexListConfigStore(utils.Singleton):
    """
    This class is responsible for handling flexlist config objects.
    """

    def get_or_create_config(self, user: AbstractBaseUser) -> DjangoAdminFlexListConfig:
        """
        Get the user's flexlist config or create a new one if it doesn't exist.
        """

        flexlist_config, _ = DjangoAdminFlexListConfig.objects.get_or_create(user=user)
        return flexlist_config

    def get_config_list_fields(
        self, flexlist_config: DjangoAdminFlexListConfig, path: list[str]
    ) -> list[utils.FlexListField]:
        """
        This method returns a list of flexlist fields expected to be found within the config's JSON,
        under the given path.
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
        Update the flexlist config with the given payload.
        """

        utils.deep_update_dict(flexlist_config.config, payload)
        flexlist_config.save(update_fields=["config"])
        return flexlist_config
