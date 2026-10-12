"""Tables, QR tokens and table sessions.

A QR token identifies an intended table + branch for the public menu. It never
grants access to owner/staff dashboards (docs/PRD.md §9.2). Each checkout still
creates its own order; a session only groups orders from one visit.
"""

import uuid

from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class TableStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    INACTIVE = "INACTIVE", "Nonaktif"
    DISABLED = "DISABLED", "Dinonaktifkan"


class TableSessionStatus(models.TextChoices):
    OPEN = "OPEN", "Terbuka"
    CLOSED = "CLOSED", "Ditutup"
    EXPIRED = "EXPIRED", "Kedaluwarsa"


class Table(BaseModel):
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.CASCADE, related_name="tables"
    )
    table_number = models.CharField(max_length=32)
    name = models.CharField(max_length=128, blank=True)
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(
        max_length=16, choices=TableStatus.choices, default=TableStatus.ACTIVE, db_index=True
    )

    class Meta:
        ordering = ["table_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "table_number"], name="uniq_table_branch_number"
            ),
        ]

    def __str__(self) -> str:
        return self.name or f"Meja {self.table_number}"

    @property
    def can_accept_orders(self) -> bool:
        return self.status == TableStatus.ACTIVE and self.branch.can_accept_orders

    def rotate_qr_token(self) -> uuid.UUID:
        """Invalidate the current QR and issue a new token."""
        self.qr_token = uuid.uuid4()
        self.save(update_fields=["qr_token", "updated_at"])
        return self.qr_token


class TableSession(BaseModel):
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="sessions")
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="table_sessions",
    )
    status = models.CharField(
        max_length=16,
        choices=TableSessionStatus.choices,
        default=TableSessionStatus.OPEN,
        db_index=True,
    )
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["table", "status"])]

    def __str__(self) -> str:
        return f"Sesi {self.table} ({self.status})"
