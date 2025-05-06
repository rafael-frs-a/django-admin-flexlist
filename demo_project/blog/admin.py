from blog.models import Comment, Post, Tag
from django.contrib import admin

from django_admin_flexlist import FlexListAdmin


@admin.register(Post)
class PostAdmin(FlexListAdmin):
    list_display = (
        "title",
        "author",
    )
    list_filter = ("tags",)
    search_fields = ("title", "content")


@admin.register(Comment)
class CommentAdmin(FlexListAdmin):
    list_display = ("post", "author")
    search_fields = ("text",)


@admin.register(Tag)
class TagAdmin(FlexListAdmin):
    list_display = ("name",)
    search_fields = ("name",)
