"""Payments, refunds and provider webhook idempotency."""

import hashlib
from decimal import Decimal

import pytest
from django.conf import settings

from apps.orders import services as order_services
from apps.orders.models import PaymentStatus
from apps.payments import services as payment_services
from apps.payments.models import (
    PaymentMethod,
    PaymentWebhookEvent,
    RefundStatus,
)
from apps.payments.providers.midtrans import map_transaction_status
from apps.payments.webhooks import process_midtrans_notification


def _order(branch, branch_product, table, method=PaymentMethod.CASH, quantity=1):
    order, _ = order_services.checkout(
        branch=branch,
        table=table,
        items=[{"branch_product_id": branch_product.id, "quantity": quantity}],
        payment_method=method,
    )
    return order


def _signed_payload(order_id, *, status="settlement", gross="15000.00", status_code="200"):
    signature = hashlib.sha512(
        f"{order_id}{status_code}{gross}{settings.MIDTRANS_SERVER_KEY}".encode()
    ).hexdigest()
    return {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross,
        "transaction_status": status,
        "transaction_id": f"tx-{order_id}",
        "signature_key": signature,
    }


@pytest.mark.django_db
def test_cash_confirmation_is_idempotent(branch, branch_product, table, cashier):
    order = _order(branch, branch_product, table)
    payment = order.payments.get()

    payment_services.confirm_cash_payment(payment=payment, actor=cashier)
    payment_services.confirm_cash_payment(payment=payment, actor=cashier)

    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == PaymentStatus.PAID
    assert order.payment_status == PaymentStatus.PAID
    # Only one attempt is recorded despite two calls.
    assert payment.attempts.count() == 1


@pytest.mark.django_db
def test_refund_cannot_exceed_refundable(branch, branch_product, table, cashier):
    order = _order(branch, branch_product, table)
    payment = order.payments.get()
    payment_services.confirm_cash_payment(payment=payment, actor=cashier)

    with pytest.raises(payment_services.PaymentError):
        payment_services.request_refund(
            payment=payment, actor=cashier, amount=Decimal("999999"), reason="salah"
        )


@pytest.mark.django_db
def test_multiple_refunds_cannot_exceed_total(branch, branch_product, table, cashier):
    order = _order(branch, branch_product, table)
    payment = order.payments.get()
    payment_services.confirm_cash_payment(payment=payment, actor=cashier)

    payment_services.request_refund(
        payment=payment, actor=cashier, amount=Decimal("15000"), reason="penuh"
    )
    with pytest.raises(payment_services.PaymentError):
        payment_services.request_refund(
            payment=payment, actor=cashier, amount=Decimal("1"), reason="lagi"
        )


@pytest.mark.django_db
def test_refund_threshold_uses_policy_setting(branch, branch_product, table):
    assert payment_services.refund_requires_manager_approval(
        settings.REFUND_CASHIER_MAX_AMOUNT + Decimal("1")
    )
    assert not payment_services.refund_requires_manager_approval(Decimal("1000"))


def test_provider_status_mapping():
    assert map_transaction_status("settlement") == PaymentStatus.PAID
    assert map_transaction_status("capture", "accept") == PaymentStatus.PAID
    assert map_transaction_status("capture", "challenge") == PaymentStatus.PENDING
    assert map_transaction_status("expire") == PaymentStatus.EXPIRED
    assert map_transaction_status("deny") == PaymentStatus.FAILED


@pytest.mark.django_db
def test_webhook_ignores_invalid_signature(branch, branch_product, table):
    order = _order(branch, branch_product, table, method=PaymentMethod.DIGITAL)
    payment = order.payments.get()
    payment.provider_reference = f"PT-{payment.id}"
    payment.save(update_fields=["provider_reference"])

    payload = {
        "order_id": f"PT-{payment.id}",
        "status_code": "200",
        "gross_amount": "15000.00",
        "transaction_status": "settlement",
        "transaction_id": "tx-1",
        "signature_key": "tidak-valid",
    }
    event = process_midtrans_notification(payload)

    payment.refresh_from_db()
    assert event.signature_valid is False
    assert payment.status != PaymentStatus.PAID


@pytest.mark.django_db
def test_webhook_marks_paid_and_is_idempotent(branch, branch_product, table):
    order = _order(branch, branch_product, table, method=PaymentMethod.DIGITAL)
    payment = order.payments.get()
    payment.provider_reference = f"PT-{payment.id}"
    payment.save(update_fields=["provider_reference"])

    payload = _signed_payload(f"PT-{payment.id}")

    first = process_midtrans_notification(payload)
    second = process_midtrans_notification(payload)

    payment.refresh_from_db()
    order.refresh_from_db()
    assert first.id == second.id
    assert PaymentWebhookEvent.objects.count() == 1
    assert payment.status == PaymentStatus.PAID
    assert order.payment_status == PaymentStatus.PAID
    assert payment.attempts.count() == 1


@pytest.mark.django_db
def test_duplicate_webhook_does_not_downgrade_paid(branch, branch_product, table):
    order = _order(branch, branch_product, table, method=PaymentMethod.DIGITAL)
    payment = order.payments.get()
    payment.provider_reference = f"PT-{payment.id}"
    payment.save(update_fields=["provider_reference"])

    process_midtrans_notification(_signed_payload(f"PT-{payment.id}", status="settlement"))
    # A later, stale "expire" notification must not undo the success.
    process_midtrans_notification(_signed_payload(f"PT-{payment.id}", status="expire"))

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PAID


@pytest.mark.django_db
def test_refund_lifecycle(branch, branch_product, table, cashier, owner):
    order = _order(branch, branch_product, table)
    payment = order.payments.get()
    payment_services.confirm_cash_payment(payment=payment, actor=cashier)

    refund = payment_services.request_refund(
        payment=payment, actor=cashier, amount=Decimal("15000"), reason="salah pesan"
    )
    assert refund.status == RefundStatus.REQUESTED

    payment_services.approve_refund(refund=refund, actor=owner)
    payment_services.complete_refund(refund=refund, actor=cashier)
    refund.refresh_from_db()
    assert refund.status == RefundStatus.SUCCEEDED
    # The original payment stays PAID after a refund.
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PAID
