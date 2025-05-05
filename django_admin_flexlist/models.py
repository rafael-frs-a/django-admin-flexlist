import typing as t

from django.conf import settings
from django.db import models

if t.TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


class DjangoAdminFlexListConfig(models.Model):
    """
    Stores user-specific configuration for the flexlist functionality.

    Uses a JSON field to store configuration data, which allows for flexible schema
    changes without requiring database migrations. The expected JSON structure is
    defined in the schema files under the `schemas` directory.

    Attributes:
        user: One-to-one relationship with the user model
        config: JSON field storing the user's flexlist configuration
    """

    user: "models.OneToOneField[AbstractUser]" = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    config = models.JSONField(default=dict)
