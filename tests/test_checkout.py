"""Checkout: snapshot pricing, stock reservation and idempotency."""

from decimal import Decimal

import pytest

from apps.inventory.models import ReservationStatus, StockReservation
from apps.inventory.services import InsufficientStock
from apps.orders import services as order_services
from apps.orders.models import Order, OrderStatus
from apps.payments.models import PaymentMethod


def _items(branch_product, quantity=2, variant=None):
    return [
        {
            "branch_product_id": branch_product.id,
            "variant_id": variant.id if variant else None,
            "quantity": quantity,
        }
    ]


@pytest.mark.django_db
def test_checkout_creates_order_with_price_snapshot(branch, branch_product, table, variant):
    order, created = order_services.checkout(
        branch=branch,
        table=table,
        items=_items(branch_product, quantity=2, variant=variant),
        payment_method=PaymentMethod.CASH,
    )

    assert created is True
    assert order.order_status == OrderStatus.PENDING
    item = order.items.get()
    # branch price 15000 + variant delta 3000 = 18000, snapshot survives menu edits.
    assert item.unit_price == Decimal("18000.00")
    assert item.subtotal == Decimal("36000.00")
    assert item.product_name_snapshot == "Kopi Susu"
    assert item.variant_name_snapshot == "Large"
    assert order.total == Decimal("36000.00")


@pytest.mark.django_db
def test_checkout_reserves_stock(branch, branch_product, table):
    order_services.checkout(
        branch=branch,
        table=table,
        items=_items(branch_product, quantity=3),
        payment_method=PaymentMethod.CASH,
    )

    branch_product.refresh_from_db()
    assert branch_product.reserved == 3
    assert StockReservation.objects.filter(
        order__isnull=False, status=ReservationStatus.RESERVED
    ).count() == 1


@pytest.mark.django_db
def test_checkout_is_idempotent(branch, branch_product, table):
    key = "checkout-key-1"
    first, created_first = order_services.checkout(
        branch=branch,
        table=table,
        items=_items(branch_product, quantity=1),
        payment_method=PaymentMethod.CASH,
        idempotency_key=key,
    )
    second, created_second = order_services.checkout(
        branch=branch,
        table=table,
        items=_items(branch_product, quantity=1),
        payment_method=PaymentMethod.CASH,
        idempotency_key=key,
    )

    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert Order.objects.count() == 1


@pytest.mark.django_db
def test_checkout_rejects_when_stock_insufficient(branch, branch_product, table):
    with pytest.raises(InsufficientStock):
        order_services.checkout(
            branch=branch,
            table=table,
            items=_items(branch_product, quantity=99),
            payment_method=PaymentMethod.CASH,
        )

    assert Order.objects.count() == 0
    branch_product.refresh_from_db()
    assert branch_product.reserved == 0


@pytest.mark.django_db
def test_checkout_rejects_when_branch_not_accepting_orders(branch, branch_product, table):
    branch.accepts_orders = False
    branch.save(update_fields=["accepts_orders"])

    with pytest.raises(order_services.OrderError):
        order_services.checkout(
            branch=branch,
            table=table,
            items=_items(branch_product, quantity=1),
            payment_method=PaymentMethod.CASH,
        )
