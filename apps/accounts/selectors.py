"""Read queries for team and access management."""

from django.db.models import QuerySet

from apps.accounts.models import Invitation, Membership, MembershipStatus, Role


def tenant_roles(tenant) -> QuerySet[Role]:
    return Role.objects.filter(tenant=tenant).order_by("name")


def tenant_memberships(tenant) -> QuerySet[Membership]:
    return (
        Membership.objects.filter(tenant=tenant)
        .select_related("user", "role")
        .prefetch_related("branch_memberships__branch")
        .order_by("user__name")
    )


def pending_invitations(tenant) -> QuerySet[Invitation]:
    return (
        Invitation.objects.filter(tenant=tenant, status=MembershipStatus.INVITED)
        .select_related("role")
        .prefetch_related("branches")
        .order_by("-created_at")
    )


def active_owner_count(tenant) -> int:
    """How many other owners remain — used to stop locking a tenant out."""
    return Membership.objects.filter(
        tenant=tenant,
        status=MembershipStatus.ACTIVE,
        role__code="OWNER",
    ).count()
