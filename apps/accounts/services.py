"""Identity/access domain services.

Single source of truth for role seeding and membership management so onboarding,
invitations and admin tools all go through the same code path.
"""

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import (
    BranchMembership,
    Membership,
    MembershipStatus,
    Permission,
    Role,
    RolePermission,
)
from apps.accounts.roles import ALL_PERMISSIONS, SYSTEM_ROLES


def ensure_permissions() -> None:
    """Create any permission that is registered in code but missing in the DB."""
    existing = set(Permission.objects.values_list("code", flat=True))
    Permission.objects.bulk_create(
        [
            Permission(code=code, description=desc)
            for code, desc in ALL_PERMISSIONS.items()
            if code not in existing
        ],
        ignore_conflicts=True,
    )


@transaction.atomic
def seed_system_roles(tenant) -> dict[str, Role]:
    """Create the tenant's copy of the system roles and their permissions."""
    ensure_permissions()
    perms = {p.code: p for p in Permission.objects.filter(code__in=ALL_PERMISSIONS)}

    roles: dict[str, Role] = {}
    for code, (name, perm_codes) in SYSTEM_ROLES.items():
        role, _ = Role.objects.get_or_create(
            tenant=tenant, code=code, defaults={"name": name, "is_system": True}
        )
        RolePermission.objects.bulk_create(
            [
                RolePermission(role=role, permission=perms[perm_code])
                for perm_code in perm_codes
                if perm_code in perms
            ],
            ignore_conflicts=True,
        )
        roles[code] = role
    return roles


@transaction.atomic
def create_membership(
    *,
    tenant,
    user,
    role_code: str,
    status: str = MembershipStatus.ACTIVE,
    branches=None,
) -> Membership:
    """Add (or update) a user's membership in a tenant, optionally scoping branches."""
    role = Role.objects.get(tenant=tenant, code=role_code)
    membership, _ = Membership.objects.get_or_create(
        tenant=tenant, user=user, defaults={"role": role, "status": status}
    )
    membership.role = role
    membership.status = status
    if status == MembershipStatus.ACTIVE and membership.joined_at is None:
        membership.joined_at = timezone.now()
    membership.save(update_fields=["role", "status", "joined_at"])

    for branch in branches or []:
        # A branch outside the tenant must never be granted.
        if branch.tenant_id != tenant.id:
            raise ValueError("Branch tidak berada di tenant yang sama.")
        BranchMembership.objects.get_or_create(membership=membership, branch=branch)

    return membership
