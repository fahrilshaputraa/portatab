"""Reusable order read queries.

Querysets are always branch/tenant scoped by the caller so no view can forget
isolation. Kitchen eligibility is expressed in SQL (not Python filtering) so it
stays efficient.
"""

from django.db.models import Q, QuerySet

from apps.orders.models import KITCHEN_ACTIVE_STATUSES, Order, OrderStatus, PaymentStatus


def branch_orders(*, branch, statuses=None) -> QuerySet[Order]:
    query = Order.objects.filter(branch=branch).select_related("table", "customer")
    if statuses:
        query = query.filter(order_status__in=statuses)
    return query


def cashier_queue(*, branch) -> QuerySet[Order]:
    """Orders the cashier must act on: pending decisions plus in-flight ones."""
    return branch_orders(branch=branch).exclude(
        order_status__in=[OrderStatus.COMPLETED, OrderStatus.REJECTED, OrderStatus.CANCELLED]
    )


def pending_orders(*, branch) -> QuerySet[Order]:
    return branch_orders(branch=branch, statuses=[OrderStatus.PENDING]).order_by("pending_since")


def kitchen_queue(*, branch) -> QuerySet[Order]:
    """Orders the kitchen may work on: digital orders only once PAID, cash allowed early."""
    return (
        branch_orders(branch=branch, statuses=list(KITCHEN_ACTIVE_STATUSES))
        .filter(
            Q(payment_status=PaymentStatus.PAID)
            | (
                Q(payment_status__in=[PaymentStatus.UNPAID, PaymentStatus.FAILED])
                & Q(payments__method="CASH")
            )
        )
        .distinct()
        .order_by("confirmed_at", "created_at")
    )
