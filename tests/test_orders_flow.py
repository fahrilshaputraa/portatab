"""Order state machine, kitchen payment gate and cashier timers."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.inventory.models import ReservationStatus
from apps.orders import services as order_services
from apps.orders.models import KITCHEN_ACTIVE_STATUSES, OrderStatus
from apps.payments import services as payment_services
from apps.payments.models import PaymentMethod


def _make_order(branch, branch_product, table, *, method=PaymentMethod.CASH, quantity=1):
    order, _ = order_services.checkout(
        branch=branch,
        table=table,
        items=[{"branch_product_id": branch_product.id, "quantity": quantity}],
        payment_method=method,
    )
    return order


@pytest.mark.django_db
def test_valid_transition_accept_then_prepare_then_ready(
    branch, branch_product, table, cashier
):
    order = _make_order(branch, branch_product, table)
    order_services.accept_order(order=order, actor=cashier)
    order.refresh_from_db()
    assert order.order_status == OrderStatus.CONFIRMED

    # Cash order may enter the kitchen before payment.
    order_services.start_preparing(order=order, actor=cashier)
    order.refresh_from_db()
    assert order.order_status == OrderStatus.PREPARING
    assert order.order_status in KITCHEN_ACTIVE_STATUSES


@pytest.mark.django_db
def test_invalid_transition_is_rejected(branch, branch_product, table, cashier):
    order = _make_order(branch, branch_product, table)
    with pytest.raises(order_services.InvalidOrderTransition):
        order_services.mark_ready(order=order, actor=cashier)


@pytest.mark.django_db
def test_digital_order_cannot_enter_kitchen_before_payment(
    branch, branch_product, table, cashier
):
    order = _make_order(branch, branch_product, table, method=PaymentMethod.DIGITAL)
    order_services.accept_order(order=order, actor=cashier)

    with pytest.raises(order_services.PaymentNotVerified):
        order_services.start_preparing(order=order, actor=cashier)


@pytest.mark.django_db
def test_digital_order_enters_kitchen_once_paid(branch, branch_product, table, cashier):
    order = _make_order(branch, branch_product, table, method=PaymentMethod.DIGITAL)
    order_services.accept_order(order=order, actor=cashier)

    payment = order.payments.get()
    payment_services.apply_provider_status(
        payment=payment, new_status="PAID", provider_reference="tx-1"
    )

    order.refresh_from_db()
    order_services.start_preparing(order=order, actor=cashier)
    order.refresh_from_db()
    assert order.order_status == OrderStatus.PREPARING


@pytest.mark.django_db
def test_rejection_releases_stock_reservation(branch, branch_product, table, cashier):
    order = _make_order(branch, branch_product, table, quantity=4)
    branch_product.refresh_from_db()
    assert branch_product.reserved == 4

    order = order_services.reject_order(order=order, actor=cashier, reason="Habis")
    branch_product.refresh_from_db()
    assert branch_product.reserved == 0
    assert order.stock_reservations.get().status == ReservationStatus.RELEASED
    assert order.rejection_reason == "Habis"


@pytest.mark.django_db
def test_starting_preparation_consumes_stock(branch, branch_product, table, cashier):
    order = _make_order(branch, branch_product, table, quantity=2)
    order_services.accept_order(order=order, actor=cashier)
    order_services.start_preparing(order=order, actor=cashier)

    branch_product.refresh_from_db()
    assert branch_product.on_hand == 8
    assert branch_product.reserved == 0


@pytest.mark.django_db
def test_pending_timers_warn_then_mark_late(branch, branch_product, table):
    order = _make_order(branch, branch_product, table)
    order.pending_since = timezone.now() - timedelta(seconds=200)
    order.save(update_fields=["pending_since"])

    result = order_services.evaluate_pending_orders(branch=branch)
    order.refresh_from_db()
    assert result["warned"] == 1
    assert order.warned_at is not None
    assert order.is_late is False

    order.pending_since = timezone.now() - timedelta(seconds=400)
    order.save(update_fields=["pending_since"])
    result = order_services.evaluate_pending_orders(branch=branch)
    order.refresh_from_db()
    assert result["late"] == 1
    assert order.is_late is True
    # Late orders are never auto-cancelled.
    assert order.order_status == OrderStatus.PENDING
