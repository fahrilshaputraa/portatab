"""Template context for platform-admin awareness."""

from apps.platform_admin.permissions import is_platform_admin


def platform_admin_context(request):
    return {"is_platform_admin": is_platform_admin(getattr(request, "user", None))}
