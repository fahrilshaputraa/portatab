"""Notification events delivered to staff dashboards.

Kept as durable rows so a realtime delivery failure never invalidates a
committed order (docs/BUSINESS-RULES.md §15). The unique constraint makes
re-processing the same event idempotent.
"""

from django.db import models

from apps.core.models import BaseModel


class NotificationEventType(models.TextChoices):
    ORDER_NEW = "ORDER_NEW", "Order baru"
    ORDER_WARNING = "ORDER_WARNING", "Order belum direspons"
    ORDER_LATE = "ORDER_LATE", "Order terlambat"
    ORDER_KITCHEN_READY = "ORDER_KITCHEN_READY", "Order masuk dapur"
    ORDER_READY = "ORDER_READY", "Order siap disajikan"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS", "Pembayaran berhasil"
    PAYMENT_FAILED = "PAYMENT_FAILED", "Pembayaran gagal"
    REFUND_FOLLOWUP = "REFUND_FOLLOWUP", "Refund perlu tindak lanjut"


class Notification(BaseModel):
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notifications"
    )
    branch = models.ForeignKey(
        "tenants.Branch",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    event_type = models.CharField(max_length=32, choices=NotificationEventType.choices, db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event_type", "order"],
                name="uniq_notification_user_event_order",
            ),
        ]
        indexes = [models.Index(fields=["user", "read_at"])]

    def __str__(self) -> str:
        return f"{self.event_type} -> {self.user_id}"

    @property
    def is_read(self) -> bool:
        return self.read_at is not None
