from django.contrib import admin

from apps.tables.models import Table, TableSession


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("table_number", "name", "branch", "status")
    list_filter = ("status",)
    search_fields = ("table_number", "name", "qr_token")


@admin.register(TableSession)
class TableSessionAdmin(admin.ModelAdmin):
    list_display = ("table", "status", "started_at", "ended_at")
    list_filter = ("status",)
