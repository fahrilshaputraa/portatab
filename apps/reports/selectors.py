"""Reporting queries.

Every figure is scoped to an authorized tenant/branch by the caller. Definitions
follow docs/BUSINESS-RULES.md §16: gross = pre-discount, net = after discount
adjusted for successful refunds; unpaid orders are never counted as collected.
"""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, Q, Sum

from apps.orders.models import Order, OrderStatus, PaymentStatus
from apps.payments.models import Refund, RefundStatus


def scoped_orders(*, tenant=None, branch=None, start=None, end=None):
    """Orders visible within the requested scope and date range."""
    query = Order.objects.all()
    if branch is not None:
        query = query.filter(branch=branch)
    elif tenant is not None:
        query = query.filter(branch__tenant=tenant)
    if start is not None:
        query = query.filter(created_at__date__gte=start)
    if end is not None:
        query = query.filter(created_at__date__lte=end)
    return query


def sales_summary(*, tenant=None, branch=None, start=None, end=None) -> dict:
    orders = scoped_orders(tenant=tenant, branch=branch, start=start, end=end)
    completed = orders.filter(order_status=OrderStatus.COMPLETED)

    totals = completed.aggregate(
        gross=Sum("subtotal"),
        discounts=Sum("discount_total"),
        net=Sum("total"),
        count=Count("id"),
    )
    gross = totals["gross"] or Decimal("0.00")
    discounts = totals["discounts"] or Decimal("0.00")
    net = totals["net"] or Decimal("0.00")

    paid = (
        completed.filter(payment_status=PaymentStatus.PAID).aggregate(total=Sum("total"))["total"]
        or Decimal("0.00")
    )
    unpaid = (
        completed.exclude(payment_status=PaymentStatus.PAID).aggregate(total=Sum("total"))["total"]
        or Decimal("0.00")
    )
    refunded = (
        Refund.objects.filter(
            payment__order__in=completed, status=RefundStatus.SUCCEEDED
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    return {
        "order_count": totals["count"] or 0,
        "gross_sales": gross,
        "discounts": discounts,
        "net_sales": net,
        "paid_amount": paid,
        "unpaid_amount": unpaid,
        "refunded_amount": refunded,
        "net_after_refund": net - refunded,
        "cancelled_count": orders.filter(
            order_status__in=[OrderStatus.CANCELLED, OrderStatus.REJECTED]
        ).count(),
    }


def payment_method_breakdown(*, tenant=None, branch=None, start=None, end=None):
    orders = scoped_orders(tenant=tenant, branch=branch, start=start, end=end).filter(
        order_status=OrderStatus.COMPLETED
    )
    return (
        orders.values("payments__method")
        .annotate(total=Sum("total"), orders=Count("id"))
        .order_by("payments__method")
    )


def top_products(*, tenant=None, branch=None, start=None, end=None, limit: int = 10):
    orders = scoped_orders(tenant=tenant, branch=branch, start=start, end=end).filter(
        order_status=OrderStatus.COMPLETED
    )
    return (
        orders.values("items__product_name_snapshot")
        .annotate(quantity=Sum("items__quantity"), revenue=Sum("items__subtotal"))
        .order_by("-quantity")[:limit]
    )


def unpaid_orders(*, tenant=None, branch=None, start=None, end=None):
    return scoped_orders(tenant=tenant, branch=branch, start=start, end=end).filter(
        Q(order_status=OrderStatus.COMPLETED) & ~Q(payment_status=PaymentStatus.PAID)
    )
