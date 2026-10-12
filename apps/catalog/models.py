"""Menu domain: categories, products, variants and per-branch configuration.

Prices are stored as ``Decimal`` (never float). The authoritative unit price for
a branch is ``BranchProduct.price + variant.price_delta``, optionally overridden
by ``BranchProductVariant.price_override`` (docs/BUSINESS-RULES.md §4). Stock
counters live on ``BranchProduct`` because inventory is tracked per branch; the
``inventory`` app owns every stock change.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import BaseModel


class ProductStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    INACTIVE = "INACTIVE", "Nonaktif"


class Category(BaseModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="categories"
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"], name="uniq_category_tenant_name"),
        ]

    def __str__(self) -> str:
        return self.name


class Product(BaseModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=16, choices=ProductStatus.choices, default=ProductStatus.ACTIVE, db_index=True
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [models.Index(fields=["tenant", "status"])]

    def __str__(self) -> str:
        return self.name

    @property
    def is_active(self) -> bool:
        return self.status == ProductStatus.ACTIVE


class ProductVariant(BaseModel):
    """A selectable option of a product (Regular, Large, Iced, ...)."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=128)
    price_delta = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["product", "name"], name="uniq_variant_product_name"),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — {self.name}"


class BranchProduct(BaseModel):
    """Makes a product sellable at a branch, with its branch price and stock."""

    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.CASCADE, related_name="branch_products"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="branch_products"
    )
    price = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    on_hand = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    track_stock = models.BooleanField(default=False)

    class Meta:
        ordering = ["product__sort_order", "product__name"]
        constraints = [
            models.UniqueConstraint(fields=["branch", "product"], name="uniq_branch_product"),
            models.CheckConstraint(
                condition=models.Q(reserved__gte=0), name="branchproduct_reserved_non_negative"
            ),
        ]
        indexes = [models.Index(fields=["branch", "is_available"])]

    def __str__(self) -> str:
        return f"{self.product.name} @ {self.branch.name}"

    @property
    def available(self) -> int:
        """Sellable quantity: ``on_hand - reserved`` (docs/BUSINESS-RULES.md §11)."""
        return self.on_hand - self.reserved

    @property
    def is_sellable(self) -> bool:
        if not (self.is_available and self.product.status == ProductStatus.ACTIVE):
            return False
        return not self.track_stock or self.available > 0


class BranchProductVariant(BaseModel):
    """Optional per-branch override of a variant's availability and price."""

    branch_product = models.ForeignKey(
        BranchProduct, on_delete=models.CASCADE, related_name="variant_overrides"
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="branch_overrides"
    )
    price_override = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch_product", "variant"], name="uniq_branch_product_variant"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.branch_product} / {self.variant.name}"
