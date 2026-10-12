"""Ordering domain: orders, order-item snapshots and status history.

Order status and payment status are separate concepts and are never encoded in
one another (docs/BUSINESS-RULES.md §7). Item rows snapshot every
transaction-relevant value so later menu edits cannot change history.
"""

from decimal import Decimal

from django.db import models

from apps.core.models import BaseModel, UUIDModel


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Menunggu kasir"
    CONFIRMED = "CONFIRMED", "Diterima"
    PREPARING = "PREPARING", "Diproses"
    READY = "READY", "Siap"
    COMPLETED = "COMPLETED", "Selesai"
    REJECTED = "REJECTED", "Ditolak"
    CANCELLED = "CANCELLED", "Dibatalkan"


class PaymentStatus(models.TextChoices):
    UNPAID = "UNPAID", "Belum dibayar"
    PENDING = "PENDING", "Menunggu pembayaran"
    PAID = "PAID", "Dibayar"
    FAILED = "FAILED", "Gagal"
    EXPIRED = "EXPIRED", "Kedaluwarsa"


class OrderSource(models.TextChoices):
    QR = "QR", "QR pelanggan"
    CASHIER = "CASHIER", "Kasir"


# Allowed order status transitions (docs/BUSINESS-RULES.md §7). Anything else is
# rejected by the backend. Late is metadata, not a status.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.REJECTED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY},
    OrderStatus.READY: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.REJECTED: set(),
    OrderStatus.CANCELLED: set(),
}

# Statuses that occupy (or will occupy) kitchen capacity.
KITCHEN_ACTIVE_STATUSES = {OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY}


class Order(BaseModel):
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.PROTECT, related_name="orders"
    )
    table = models.ForeignKey(
        "tables.Table", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    table_session = models.ForeignKey(
        "tables.TableSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_orders",
    )

    order_number = models.CharField(max_length=32)
    order_status = models.CharField(
        max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True
    )
    payment_status = models.CharField(
        max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID, db_index=True
    )
    order_source = models.CharField(
        max_length=16, choices=OrderSource.choices, default=OrderSource.QR
    )

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    service_charge = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    customer_note = models.TextField(blank=True)

    is_late = models.BooleanField(default=False)
    pending_since = models.DateTimeField(db_index=True)
    late_since = models.DateTimeField(null=True, blank=True)
    warned_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Makes a retried checkout resolve to the same order instead of a duplicate
    # (docs/PRD.md §6, docs/API-CONVENTIONS.md §10).
    idempotency_key = models.CharField(max_length=64, null=True, blank=True, unique=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "order_number"], name="uniq_order_branch_number"
            ),
            models.CheckConstraint(
                condition=models.Q(total__gte=0), name="order_total_non_negative"
            ),
        ]
        indexes = [
            models.Index(fields=["branch", "order_status"]),
            models.Index(fields=["branch", "created_at"]),
            models.Index(fields=["order_status", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.order_number

    @property
    def can_enter_kitchen(self) -> bool:
        """Digital orders enter the kitchen only once payment is verified PAID.

        Cash orders may enter earlier, but only when the tenant's operational
        policy permits it (docs/BUSINESS-RULES.md §8).
        """
        if self.order_status not in KITCHEN_ACTIVE_STATUSES:
            return False
        if self.payment_status == PaymentStatus.PAID:
            return True
        if self.payment_status in {PaymentStatus.UNPAID, PaymentStatus.FAILED}:
            if not self.payment_method_is_cash:
                return False
            # Imported lazily to keep the model free of service imports.
            from apps.tenants.services import cash_orders_to_kitchen

            return cash_orders_to_kitchen(self.branch.tenant)
        return False

    @property
    def payment_method_is_cash(self) -> bool:
        payment = self.payments.order_by("-created_at").first()
        return bool(payment and payment.method == "CASH")

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in ALLOWED_TRANSITIONS.get(self.order_status, set())


class OrderItem(UUIDModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items"
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )

    product_name_snapshot = models.CharField(max_length=255)
    variant_name_snapshot = models.CharField(max_length=128, blank=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    quantity = models.PositiveIntegerField()
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True)
    options_snapshot = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="orderitem_qty_positive"),
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=0), name="orderitem_subtotal_non_negative"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.product_name_snapshot}"


class OrderStatusHistory(UUIDModel):
    """Audit trail of order status changes (docs/BUSINESS-RULES.md §7)."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    changed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_status_changes",
    )
    from_status = models.CharField(max_length=16, choices=OrderStatus.choices, blank=True)
    to_status = models.CharField(max_length=16, choices=OrderStatus.choices)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "order status histories"

    def __str__(self) -> str:
        return f"{self.order_id}: {self.from_status} -> {self.to_status}"
