"""Platform administration services."""

from django.db import transaction

from apps.platform_admin.models import PlatformAdminMembership, PlatformAdminRole
from apps.tenants.services import record_audit

SUPERADMIN_CODE = "SUPERADMIN"


def ensure_platform_admin_role(*, code: str = SUPERADMIN_CODE, name: str = "Super Admin"):
    role, _ = PlatformAdminRole.objects.get_or_create(code=code, defaults={"name": name})
    return role


@transaction.atomic
def grant_platform_admin(user, *, actor=None, code: str = SUPERADMIN_CODE):
    """Give a user platform-admin access (idempotent)."""
    role = ensure_platform_admin_role(code=code)
    membership, created = PlatformAdminMembership.objects.get_or_create(
        user=user, role=role
    )
    if created:
        record_audit(action="platform_admin.granted", user=actor, entity=membership)
    return membership
