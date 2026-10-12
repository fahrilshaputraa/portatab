"""Platform-admin authorization.

Platform admins are separate from tenant owners (docs/BUSINESS-RULES.md §2) and
never gain tenant access by virtue of being an admin. These helpers gate the
platform portal (content management, tenant administration).
"""

from functools import wraps

from django.core.exceptions import PermissionDenied

from apps.platform_admin.models import PlatformAdminMembership, PlatformAdminStatus


def is_platform_admin(user) -> bool:
    """True for Django staff/superusers or active platform-admin members."""
    if user is None or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return PlatformAdminMembership.objects.filter(
        user=user, status=PlatformAdminStatus.ACTIVE
    ).exists()


def require_platform_admin(view):
    """Decorator for views that only platform admins may reach."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not is_platform_admin(request.user):
            raise PermissionDenied("Hanya admin platform yang boleh mengakses halaman ini.")
        return view(request, *args, **kwargs)

    return wrapper
