from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "event_type", "title", "branch", "read_at", "created_at")
    list_filter = ("event_type",)
    search_fields = ("title",)
