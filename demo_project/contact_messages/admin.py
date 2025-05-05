from contact_messages.models import ContactMessage
from django.contrib import admin

from django_admin_flexlist import FlexListAdmin


@admin.register(ContactMessage)
class ContactMessageAdmin(FlexListAdmin):
    list_display = ("name", "email", "subject")
    search_fields = ("name", "email", "subject", "message")
