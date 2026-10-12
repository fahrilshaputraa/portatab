from django.contrib import admin

from apps.platform_admin.models import PlatformAdminMembership, PlatformAdminRole


@admin.register(PlatformAdminRole)
class PlatformAdminRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code")


@admin.register(PlatformAdminMembership)
class PlatformAdminMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "status", "created_at")
    list_filter = ("status",)
