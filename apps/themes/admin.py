from django.contrib import admin

from apps.themes.models import (
    MediaAsset,
    TenantTheme,
    ThemeAuditLog,
    ThemePublication,
    ThemeTemplate,
)


@admin.register(ThemeTemplate)
class ThemeTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "template_key", "version", "minimum_plan", "status")
    list_filter = ("status",)


class ThemePublicationInline(admin.TabularInline):
    model = ThemePublication
    extra = 0


@admin.register(TenantTheme)
class TenantThemeAdmin(admin.ModelAdmin):
    list_display = ("tenant", "template", "status", "updated_at")
    list_filter = ("status",)
    inlines = [ThemePublicationInline]


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("tenant", "original_filename", "media_type", "created_at")


@admin.register(ThemeAuditLog)
class ThemeAuditLogAdmin(admin.ModelAdmin):
    list_display = ("tenant_theme", "action", "actor", "created_at")
    list_filter = ("action",)
