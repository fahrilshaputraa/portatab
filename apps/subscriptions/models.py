"""SaaS subscriptions, invoices and PortaTap vouchers.

A subscription belongs to a tenant, never to a staff account. Invoice rows keep a
price snapshot so a plan price change never rewrites history
(docs/BUSINESS-RULES.md §13). Subscription billing is separate from customer
order payments.
"""

from decimal import Decimal

from django.db import models

from apps.core.models import BaseModel, UUIDModel


class SubscriptionStatus(models.TextChoices):
    TRIALING = "TRIALING", "Masa percobaan"
    ACTIVE = "ACTIVE", "Aktif"
    PAST_DUE = "PAST_DUE", "Menunggak"
    CANCELLED = "CANCELLED", "Dibatalkan"
    EXPIRED = "EXPIRED", "Kedaluwarsa"


class PlanStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    INACTIVE = "INACTIVE", "Nonaktif"


class InvoiceStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ISSUED = "ISSUED", "Diterbitkan"
    PAID = "PAID", "Dibayar"
    OVERDUE = "OVERDUE", "Jatuh tempo"
    VOID = "VOID", "Dibatalkan"


class VoucherStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    INACTIVE = "INACTIVE", "Nonaktif"
    EXPIRED = "EXPIRED", "Kedaluwarsa"


class Plan(BaseModel):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=64, unique=True)
    monthly_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    max_branches = models.PositiveIntegerField(default=1)
    max_accounts = models.PositiveIntegerField(default=5)
    features = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16, choices=PlanStatus.choices, default=PlanStatus.ACTIVE
    )

    class Meta:
        ordering = ["monthly_price", "name"]

    def __str__(self) -> str:
        return self.name


class Subscription(BaseModel):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(
        max_length=16,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIALING,
        db_index=True,
    )
    current_period_start = models.DateField(null=True, blank=True)
    current_period_end = models.DateField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # One active subscription per tenant at a time; history is kept as rows
            # with other statuses.
            models.UniqueConstraint(
                fields=["tenant"],
                condition=models.Q(status__in=["TRIALING", "ACTIVE", "PAST_DUE"]),
                name="uniq_active_subscription_per_tenant",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.plan.code} [{self.status}]"


class SubscriptionInvoice(BaseModel):
    subscription = models.ForeignKey(
        Subscription, on_delete=models.PROTECT, related_name="invoices"
    )
    invoice_number = models.CharField(max_length=32, unique=True)
    normal_amount = models.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default="IDR")
    status = models.CharField(
        max_length=16, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT, db_index=True
    )
    price_snapshot = models.JSONField(null=True, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.invoice_number


class SubscriptionPayment(UUIDModel):
    invoice = models.ForeignKey(
        SubscriptionInvoice, on_delete=models.PROTECT, related_name="payments"
    )
    provider = models.CharField(max_length=32, blank=True)
    provider_reference = models.CharField(max_length=128, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=16, default="PENDING")
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.invoice_id}:{self.amount} [{self.status}]"


class SubscriptionVoucher(BaseModel):
    code = models.CharField(max_length=64, unique=True)
    discount_type = models.CharField(max_length=16)
    discount_value = models.DecimalField(max_digits=14, decimal_places=2)
    duration_months = models.PositiveIntegerField(default=1)
    quota = models.PositiveIntegerField(null=True, blank=True)
    redemption_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=VoucherStatus.choices, default=VoucherStatus.ACTIVE
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class SubscriptionVoucherRedemption(UUIDModel):
    voucher = models.ForeignKey(
        SubscriptionVoucher, on_delete=models.PROTECT, related_name="redemptions"
    )
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="voucher_redemptions"
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="voucher_redemptions"
    )
    status = models.CharField(max_length=16, default="REDEEMED")
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-redeemed_at"]
        constraints = [
            # An early-adopter voucher is once per tenant unless a promo says otherwise.
            models.UniqueConstraint(
                fields=["voucher", "tenant"], name="uniq_voucher_tenant_redemption"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.voucher_id} -> {self.tenant_id}"


class SubscriptionEvent(UUIDModel):
    """Append-only log of subscription lifecycle changes."""

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.subscription_id}:{self.event_type}"
