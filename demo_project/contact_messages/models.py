from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)  # type: ignore[var-annotated]
    email = models.EmailField()  # type: ignore[var-annotated]
    subject = models.CharField(max_length=200)  # type: ignore[var-annotated]
    message = models.TextField()  # type: ignore[var-annotated]
