from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)  # type: ignore[var-annotated]


class Post(models.Model):
    title = models.CharField(max_length=200)  # type: ignore[var-annotated]
    content = models.TextField()  # type: ignore[var-annotated]
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # type: ignore[var-annotated]
    tags = models.ManyToManyField(Tag, blank=True)  # type: ignore[var-annotated]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")  # type: ignore[var-annotated]
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # type: ignore[var-annotated]
    text = models.TextField()  # type: ignore[var-annotated]
