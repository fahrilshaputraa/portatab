"""Tenant customer promotions (food & beverage orders).

Separate from PortaTap subscription vouchers (docs/BUSINESS-RULES.md §12–13).
Eligibility and the final discount are always computed on the backend.
"""

from decimal import Decimal

from django.db import models

from apps.core.models import BaseModel, UUIDModel


class DiscountType(models.TextChoices):
    FIXED = "FIXED", "Nominal"
    PERCENTAGE = "PERCENTAGE", "Persentase"


class PromotionStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ACTIVE = "ACTIVE", "Aktif"
    INACTIVE = "INACTIVE", "Nonaktif"
    EXPIRED = "EXPIRED", "Kedaluwarsa"


class RedemptionStatus(models.TextChoices):
    APPLIED = "APPLIED", "Diterapkan"
    RELEASED = "RELEASED", "Dilepas"
    CANCELLED = "CANCELLED", "Dibatalkan"


class Promotion(BaseModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="promotions"
    )
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    discount_type = models.CharField(max_length=16, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=14, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    max_discount_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    total_quota = models.PositiveIntegerField(null=True, blank=True)
    per_customer_limit = models.PositiveIntegerField(null=True, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=PromotionStatus.choices, default=PromotionStatus.DRAFT, db_index=True
    )
    branches = models.ManyToManyField(
        "tenants.Branch", related_name="promotions", blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_promotion_tenant_code"),
        ]

    def __str__(self) -> str:
        return f"{self.code} ({self.name})"


class PromotionRedemption(UUIDModel):
    """Records that a promotion was applied to an order."""

    promotion = models.ForeignKey(
        Promotion, on_delete=models.PROTECT, related_name="redemptions"
    )
    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="promotion_redemptions"
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="promotion_redemptions",
    )
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=16, choices=RedemptionStatus.choices, default=RedemptionStatus.APPLIED
    )
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-redeemed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["promotion", "order"], name="uniq_promotion_redemption_order"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.promotion_id} -> {self.order_id}"
