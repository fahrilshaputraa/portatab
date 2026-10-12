"""Branch product stock and its audit trail.

Every stock change writes a ``StockMovement`` so inventory stays auditable
(docs/BUSINESS-RULES.md §11). Reservations are tracked per order + product so a
release/consume is idempotent and never reserves the same stock twice.
"""

from django.db import models

from apps.core.models import UUIDModel


class MovementType(models.TextChoices):
    RESERVE = "RESERVE", "Reservasi"
    RELEASE = "RELEASE", "Pelepasan reservasi"
    CONSUME = "CONSUME", "Konsumsi"
    ADJUSTMENT = "ADJUSTMENT", "Koreksi"
    RESTOCK = "RESTOCK", "Penambahan stok"


class ReservationStatus(models.TextChoices):
    RESERVED = "RESERVED", "Direservasi"
    RELEASED = "RELEASED", "Dilepas"
    CONSUMED = "CONSUMED", "Dikonsumsi"
    EXPIRED = "EXPIRED", "Kedaluwarsa"


class StockReservation(UUIDModel):
    branch_product = models.ForeignKey(
        "catalog.BranchProduct", on_delete=models.CASCADE, related_name="reservations"
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="stock_reservations"
    )
    quantity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        choices=ReservationStatus.choices,
        default=ReservationStatus.RESERVED,
        db_index=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "branch_product"], name="uniq_reservation_order_product"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="reservation_qty_positive"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.branch_product_id} [{self.status}]"


class StockMovement(UUIDModel):
    """Append-only stock ledger.

    ``quantity_delta`` is the signed change this movement applies: to ``reserved``
    for RESERVE/RELEASE, and to ``on_hand`` for CONSUME/ADJUSTMENT/RESTOCK.
    ``stock_after`` is ``on_hand`` afterwards; ``reserved_after`` is ``reserved``
    afterwards, so every counter is reconstructable from the ledger.
    """

    branch_product = models.ForeignKey(
        "catalog.BranchProduct", on_delete=models.CASCADE, related_name="movements"
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    movement_type = models.CharField(max_length=16, choices=MovementType.choices, db_index=True)
    quantity_delta = models.IntegerField()
    stock_after = models.IntegerField()
    reserved_after = models.IntegerField(default=0)
    reason = models.CharField(max_length=255, blank=True)
    reference_type = models.CharField(max_length=64, blank=True)
    reference_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["branch_product", "created_at"])]

    def __str__(self) -> str:
        return f"{self.movement_type} {self.quantity_delta:+d} -> {self.stock_after}"
