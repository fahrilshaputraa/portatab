"""Payment and refund services.

Rules enforced here (docs/BUSINESS-RULES.md §8–10):

- Cash is PAID only after an authorised staff member confirms receipt.
- Digital status is only ever applied from verified provider data.
- A paid payment is never downgraded by a stale/duplicate event.
- Refunds respect the refundable balance (including in-flight refunds).
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order, OrderStatus, PaymentStatus
from apps.payments.models import (
    OPEN_REFUND_STATUSES,
    Payment,
    PaymentAttempt,
    PaymentMethod,
    PaymentProvider,
    Refund,
    RefundStatus,
)
from apps.tenants.services import record_audit

# Provider statuses that must never overwrite a PAID payment.
_NON_FINAL_OR_FAILURE = {
    PaymentStatus.PENDING,
    PaymentStatus.FAILED,
    PaymentStatus.EXPIRED,
    PaymentStatus.UNPAID,
}


class PaymentError(Exception):
    """Raised for invalid payment operations."""


def midtrans_order_id(payment: Payment) -> str:
    """Stable, unique Midtrans ``order_id`` for a payment (<= 50 chars)."""
    return payment.provider_reference or f"PT-{payment.id}"


def initiate_digital_payment(*, payment: Payment, client=None) -> dict:
    """Create a provider transaction and return ``{token, redirect_url}``.

    The browser redirect is only a hint; the payment is confirmed later from a
    verified webhook or a reconciliation poll (docs/BUSINESS-RULES.md §8).
    """
    from apps.payments.providers.midtrans import MidtransClient

    if payment.method != PaymentMethod.DIGITAL:
        raise PaymentError("Pembayaran ini bukan pembayaran digital.")
    if payment.status == PaymentStatus.PAID:
        raise PaymentError("Pembayaran sudah lunas.")

    client = client or MidtransClient.from_settings()
    order_id = midtrans_order_id(payment)
    result = client.create_snap_transaction(
        order_id=order_id,
        gross_amount=int(payment.amount),
        customer={
            "first_name": payment.order.customer.name
            if payment.order.customer
            else "Pelanggan"
        },
    )

    payment.provider_reference = order_id
    payment.status = PaymentStatus.PENDING
    payment.save(update_fields=["provider_reference", "status", "updated_at"])

    PaymentAttempt.objects.create(
        payment=payment,
        provider_reference=result.get("token", ""),
        status=PaymentStatus.PENDING,
        provider_response={"token": result.get("token"), "redirect_url": result.get("redirect_url")},
    )
    return result


def create_payment_for_order(*, order: Order, method: str) -> Payment:
    """Create the (UNPAID) payment row for a freshly checked-out order."""
    provider = (
        PaymentProvider.CASH if method == PaymentMethod.CASH else PaymentProvider.MIDTRANS
    )
    return Payment.objects.create(
        order=order,
        method=method,
        provider=provider,
        status=PaymentStatus.UNPAID,
        amount=order.total,
        currency=settings.CURRENCY_CODE,
    )


def sync_order_payment_status(order: Order) -> str:
    """Recompute ``order.payment_status`` from its payments. Single source of truth."""
    statuses = set(order.payments.values_list("status", flat=True))
    if PaymentStatus.PAID in statuses:
        new_status = PaymentStatus.PAID
    elif PaymentStatus.PENDING in statuses:
        new_status = PaymentStatus.PENDING
    elif statuses and statuses <= {PaymentStatus.FAILED, PaymentStatus.EXPIRED}:
        new_status = PaymentStatus.FAILED
    else:
        new_status = PaymentStatus.UNPAID

    if order.payment_status != new_status:
        order.payment_status = new_status
        order.save(update_fields=["payment_status", "updated_at"])
    return new_status


def _notify_if_kitchen_eligible(order: Order) -> None:
    """Tell the kitchen an order is ready to be worked on, once."""
    from apps.accounts.roles import Perm
    from apps.notifications.models import NotificationEventType
    from apps.notifications.services import notify_order_event

    if order.order_status in {OrderStatus.CONFIRMED, OrderStatus.PREPARING} and order.can_enter_kitchen:
        notify_order_event(
            order=order,
            event_type=NotificationEventType.ORDER_KITCHEN_READY,
            permission_code=Perm.ORDERS_PREPARE,
            title=f"Order {order.order_number} masuk dapur",
            message="Order sudah boleh diproses dapur.",
        )


@transaction.atomic
def confirm_cash_payment(
    *, payment: Payment, actor, amount_received: Decimal | None = None
) -> Payment:
    """Mark a cash payment as received. Idempotent against double confirmation."""
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.method != PaymentMethod.CASH:
        raise PaymentError("Hanya pembayaran tunai yang dikonfirmasi manual.")

    if payment.status == PaymentStatus.PAID:
        return payment

    if amount_received is not None and amount_received < payment.amount:
        raise PaymentError(
            f"Uang diterima ({amount_received}) kurang dari tagihan ({payment.amount})."
        )

    payment.status = PaymentStatus.PAID
    payment.paid_at = timezone.now()
    payment.confirmed_by = actor
    payment.save(update_fields=["status", "paid_at", "confirmed_by", "updated_at"])

    PaymentAttempt.objects.create(
        payment=payment,
        status=PaymentStatus.PAID,
        completed_at=timezone.now(),
        provider_response={"confirmed_by": str(actor.pk) if actor else None},
    )

    order = payment.order
    sync_order_payment_status(order)
    record_audit(
        action="payment.cash_confirmed",
        tenant=order.branch.tenant,
        user=actor,
        entity=payment,
        after={"amount": str(payment.amount), "order": order.order_number},
    )
    _notify_if_kitchen_eligible(order)
    return payment


@transaction.atomic
def apply_provider_status(
    *,
    payment: Payment,
    new_status: str,
    provider_reference: str = "",
    payload: dict | None = None,
    failure_reason: str = "",
) -> Payment:
    """Apply a verified provider status. Never downgrades a PAID payment."""
    payment = Payment.objects.select_for_update().get(pk=payment.pk)

    if payment.status == PaymentStatus.PAID and new_status in _NON_FINAL_OR_FAILURE:
        # Stale or duplicate event for an already-successful payment.
        return payment

    payment.status = new_status
    if provider_reference:
        payment.provider_reference = provider_reference
    if new_status == PaymentStatus.PAID:
        payment.paid_at = payment.paid_at or timezone.now()
    elif new_status == PaymentStatus.EXPIRED:
        payment.expired_at = timezone.now()
    payment.save(
        update_fields=[
            "status",
            "provider_reference",
            "paid_at",
            "expired_at",
            "updated_at",
        ]
    )

    PaymentAttempt.objects.create(
        payment=payment,
        provider_reference=provider_reference,
        status=new_status,
        failure_reason=failure_reason,
        provider_response=payload,
        completed_at=timezone.now(),
    )

    order = payment.order
    sync_order_payment_status(order)
    record_audit(
        action="payment.provider_status",
        tenant=order.branch.tenant,
        entity=payment,
        after={"status": new_status, "provider_reference": provider_reference},
    )
    if new_status == PaymentStatus.PAID:
        _notify_if_kitchen_eligible(order)
    return payment


def generate_refund_number() -> str:
    today = timezone.localdate()
    count = Refund.objects.filter(created_at__date=today).count()
    return f"RF-{today:%y%m%d}-{count + 1:04d}"


def refund_requires_manager_approval(amount: Decimal) -> bool:
    """Policy threshold above which a cashier may not approve on their own."""
    return amount > settings.REFUND_CASHIER_MAX_AMOUNT


@transaction.atomic
def request_refund(*, payment: Payment, actor, amount: Decimal, reason: str = "") -> Refund:
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.status != PaymentStatus.PAID:
        raise PaymentError("Refund hanya untuk pembayaran yang sudah berhasil.")

    amount = Decimal(amount)
    if amount <= 0:
        raise PaymentError("Nominal refund harus lebih dari 0.")
    if amount > payment.refundable_amount:
        raise PaymentError(
            f"Nominal refund melebihi sisa yang dapat dikembalikan ({payment.refundable_amount})."
        )

    refund = Refund.objects.create(
        payment=payment,
        requested_by=actor,
        refund_number=generate_refund_number(),
        amount=amount,
        reason=reason,
    )
    record_audit(
        action="refund.requested",
        tenant=payment.order.branch.tenant,
        user=actor,
        entity=refund,
        after={"amount": str(amount), "payment": str(payment.id)},
    )
    return refund


@transaction.atomic
def approve_refund(*, refund: Refund, actor) -> Refund:
    refund = Refund.objects.select_for_update().get(pk=refund.pk)
    if refund.status != RefundStatus.REQUESTED:
        raise PaymentError("Hanya refund berstatus REQUESTED yang dapat disetujui.")
    refund.status = RefundStatus.APPROVED
    refund.approved_by = actor
    refund.approved_at = timezone.now()
    refund.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    record_audit(
        action="refund.approved",
        tenant=refund.payment.order.branch.tenant,
        user=actor,
        entity=refund,
    )
    return refund


@transaction.atomic
def complete_refund(*, refund: Refund, actor, provider_reference: str = "") -> Refund:
    """Mark a refund successful once the money has actually been returned."""
    refund = Refund.objects.select_for_update().get(pk=refund.pk)
    if refund.status not in OPEN_REFUND_STATUSES:
        raise PaymentError("Refund tidak dalam status yang dapat diselesaikan.")
    if refund.status == RefundStatus.SUCCEEDED:
        return refund
    refund.status = RefundStatus.SUCCEEDED
    refund.provider_reference = provider_reference or refund.provider_reference
    refund.completed_at = timezone.now()
    refund.save(
        update_fields=["status", "provider_reference", "completed_at", "updated_at"]
    )
    record_audit(
        action="refund.completed",
        tenant=refund.payment.order.branch.tenant,
        user=actor,
        entity=refund,
        after={"amount": str(refund.amount)},
    )
    return refund


@transaction.atomic
def fail_refund(*, refund: Refund, actor, failure_reason: str) -> Refund:
    """A failed refund stays visible for follow-up rather than disappearing."""
    refund = Refund.objects.select_for_update().get(pk=refund.pk)
    refund.status = RefundStatus.FAILED
    refund.failure_reason = failure_reason
    refund.save(update_fields=["status", "failure_reason", "updated_at"])
    record_audit(
        action="refund.failed",
        tenant=refund.payment.order.branch.tenant,
        user=actor,
        entity=refund,
        after={"failure_reason": failure_reason},
    )
    return refund
