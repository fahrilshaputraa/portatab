"""Reusable read queries (selectors).

Keeping scoped queries here means tenant/branch isolation is written once and
reused everywhere, instead of being re-implemented per view.
"""

from django.db.models import QuerySet

from apps.accounts.models import BranchMembership, MembershipStatus
from apps.accounts.roles import TENANT_WIDE_ROLES
from apps.tenants.models import Branch, Tenant


def accessible_tenants(user) -> QuerySet[Tenant]:
    """Tenants where ``user`` has an active membership."""
    return (
        Tenant.objects.filter(
            memberships__user=user, memberships__status=MembershipStatus.ACTIVE
        )
        .distinct()
        .order_by("name")
    )


def accessible_branches(membership) -> QuerySet[Branch]:
    """Branches the membership may operate on.

    Tenant-wide roles (owner, manager) see every branch. Other roles see only the
    branches explicitly granted through ``BranchMembership``.
    """
    branches = Branch.objects.filter(tenant_id=membership.tenant_id)
    if membership.role.code in TENANT_WIDE_ROLES:
        return branches.order_by("name")
    granted = BranchMembership.objects.filter(membership=membership).values("branch_id")
    return branches.filter(id__in=granted).order_by("name")
