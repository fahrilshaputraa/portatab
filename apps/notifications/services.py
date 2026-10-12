"""Notification services.

Notifications are durable rows; the unique constraint on
(user, event_type, order) makes re-processing the same event idempotent
(docs/BUSINESS-RULES.md §15). Delivery failure never rolls back the order.
"""

from __future__ import annotations

from apps.accounts.models import Membership, MembershipStatus, User
from apps.notifications.models import Notification
from apps.tenants.selectors import accessible_branches


def staff_with_permission(*, tenant, code: str, branch=None):
    """Active members of ``tenant`` whose role grants ``code`` and who can see ``branch``."""
    memberships = (
        Membership.objects.select_related("role", "user")
        .filter(
            tenant=tenant,
            status=MembershipStatus.ACTIVE,
            role__role_permissions__permission__code=code,
        )
        .distinct()
    )

    users: list[User] = []
    for membership in memberships:
        if branch is not None and not accessible_branches(membership).filter(pk=branch.pk).exists():
            continue
        users.append(membership.user)
    return users


def notify(
    *,
    event_type: str,
    title: str,
    users,
    message: str = "",
    order=None,
    branch=None,
) -> list[Notification]:
    """Create one notification per user, skipping duplicates."""
    created: list[Notification] = []
    for user in users:
        notification, was_created = Notification.objects.get_or_create(
            user=user,
            event_type=event_type,
            order=order,
            defaults={"title": title, "message": message, "branch": branch},
        )
        if was_created:
            created.append(notification)
    return created


def notify_order_event(
    *,
    order,
    event_type: str,
    permission_code: str,
    title: str,
    message: str = "",
) -> list[Notification]:
    """Notify every staff member who can act on this order event.

    The single entry point for order notifications: recipients are resolved from
    the required permission and branch, so callers only supply wording.
    """
    recipients = staff_with_permission(
        tenant=order.branch.tenant, code=permission_code, branch=order.branch
    )
    return notify(
        event_type=event_type,
        title=title,
        message=message,
        users=recipients,
        order=order,
        branch=order.branch,
    )
