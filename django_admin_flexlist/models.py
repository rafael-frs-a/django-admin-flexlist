import typing as t

from django.conf import settings
from django.db import models

if t.TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


class DjangoAdminFlexListConfig(models.Model):
    """
    This model stores all of the package's configuration for a user in the format of a JSON field.
    This way, we reduce the chances of changing the model and having new migrations.
    The expected format for the JSON field is defined in the schema files under the `schemas` directory.
    """

    user: "models.OneToOneField[AbstractUser]" = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    config = models.JSONField(default=dict)
