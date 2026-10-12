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


def kitchen_queue(*, branch, allow_cash_before_payment: bool) -> QuerySet[Order]:
    """Orders the kitchen may work on.

    Digital orders only qualify once PAID. Cash orders qualify before payment
    only when ``allow_cash_before_payment`` (the tenant's policy) is on.
    """
    query = branch_orders(branch=branch, statuses=list(KITCHEN_ACTIVE_STATUSES))
    if allow_cash_before_payment:
        query = query.filter(
            Q(payment_status=PaymentStatus.PAID) | Q(payments__method="CASH")
        )
    else:
        query = query.filter(payment_status=PaymentStatus.PAID)
    return query.distinct().order_by("confirmed_at", "created_at")
