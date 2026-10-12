"""Customer identity for QR ordering.

Customers are optional and do not sign in (docs/PRD.md §10.1). Records are still
tenant-scoped so one business never sees another's customers.
"""

from django.db import models

from apps.core.models import BaseModel


class CustomerStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    BLOCKED = "BLOCKED", "Diblokir"


class Customer(BaseModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="customers"
    )
    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32, blank=True, db_index=True)
    email = models.EmailField(blank=True)
    status = models.CharField(
        max_length=16, choices=CustomerStatus.choices, default=CustomerStatus.ACTIVE
    )

    class Meta:
        ordering = ["name", "phone"]
        indexes = [models.Index(fields=["tenant", "phone"])]

    def __str__(self) -> str:
        return self.name or self.phone or str(self.id)


class CustomerAddress(BaseModel):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="addresses"
    )
    label = models.CharField(max_length=64, blank=True)
    address = models.TextField()
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["label"]

    def __str__(self) -> str:
        return f"{self.customer} — {self.label or 'alamat'}"
