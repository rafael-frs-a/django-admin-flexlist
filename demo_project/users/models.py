from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    dob = models.DateField(null=True, blank=True)  # type: ignore[var-annotated]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
