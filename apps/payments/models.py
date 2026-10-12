"""Payments and refunds.

A payment attempt is distinct from the order. Digital success is only accepted
after the backend verifies the provider (docs/BUSINESS-RULES.md §8). Duplicate
provider notifications are deduplicated through ``PaymentWebhookEvent.event_key``.
"""

from decimal import Decimal

from django.db import models

from apps.core.models import BaseModel, UUIDModel
from apps.orders.models import PaymentStatus  # single source of truth for the vocabulary


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Tunai"
    DIGITAL = "DIGITAL", "Digital"


class PaymentProvider(models.TextChoices):
    CASH = "CASH", "Tunai"
    MIDTRANS = "MIDTRANS", "Midtrans"


class RefundStatus(models.TextChoices):
    REQUESTED = "REQUESTED", "Diminta"
    APPROVED = "APPROVED", "Disetujui"
    PROCESSING = "PROCESSING", "Diproses"
    SUCCEEDED = "SUCCEEDED", "Berhasil"
    FAILED = "FAILED", "Gagal"
    REJECTED = "REJECTED", "Ditolak"
    CANCELLED = "CANCELLED", "Dibatalkan"


# Refund statuses that still hold (part of) the refundable balance.
OPEN_REFUND_STATUSES = {
    RefundStatus.REQUESTED,
    RefundStatus.APPROVED,
    RefundStatus.PROCESSING,
    RefundStatus.SUCCEEDED,
}


class Payment(BaseModel):
    order = models.ForeignKey(
        "orders.Order", on_delete=models.PROTECT, related_name="payments"
    )
    confirmed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_payments",
    )
    method = models.CharField(max_length=16, choices=PaymentMethod.choices)
    provider = models.CharField(
        max_length=16, choices=PaymentProvider.choices, default=PaymentProvider.CASH
    )
    status = models.CharField(
        max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID, db_index=True
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default="IDR")
    provider_reference = models.CharField(max_length=128, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=64, null=True, blank=True, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gte=0), name="payment_amount_non_negative"),
        ]
        indexes = [models.Index(fields=["order", "status"])]

    def __str__(self) -> str:
        return f"{self.method} {self.amount} [{self.status}]"

    @property
    def refunded_amount(self) -> Decimal:
        return self.refunds.filter(
            status__in=[RefundStatus.SUCCEEDED, RefundStatus.PROCESSING, RefundStatus.APPROVED]
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    @property
    def pending_refund_amount(self) -> Decimal:
        return self.refunds.filter(
            status__in=[RefundStatus.REQUESTED, RefundStatus.APPROVED, RefundStatus.PROCESSING]
        ).aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    @property
    def refundable_amount(self) -> Decimal:
        """Remaining amount that may still be refunded, accounting for in-flight refunds."""
        return self.amount - self.refunded_amount - self.pending_refund_amount


class PaymentAttempt(UUIDModel):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="attempts")
    provider_reference = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=16, choices=PaymentStatus.choices)
    failure_reason = models.TextField(blank=True)
    provider_response = models.JSONField(null=True, blank=True)
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-initiated_at"]

    def __str__(self) -> str:
        return f"attempt {self.provider_reference or self.id} [{self.status}]"


class Refund(BaseModel):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    requested_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_refunds",
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_refunds",
    )
    refund_number = models.CharField(max_length=32, unique=True)
    status = models.CharField(
        max_length=16, choices=RefundStatus.choices, default=RefundStatus.REQUESTED, db_index=True
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.CharField(max_length=255, blank=True)
    provider_reference = models.CharField(max_length=128, blank=True)
    failure_reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="refund_amount_positive"),
        ]
        indexes = [models.Index(fields=["payment", "status"])]

    def __str__(self) -> str:
        return f"{self.refund_number} [{self.status}]"


class PaymentWebhookEvent(UUIDModel):
    """Raw provider notification, stored before processing for idempotency.

    ``event_key`` is a deterministic hash of the provider payload so a replayed
    notification finds the same row instead of creating a second effect
    (docs/API-CONVENTIONS.md §10–11).
    """

    provider = models.CharField(max_length=16, choices=PaymentProvider.choices)
    event_key = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=64, blank=True)
    provider_reference = models.CharField(max_length=128, blank=True, db_index=True)
    payload = models.JSONField()
    signature_valid = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.provider}:{self.event_key}"
