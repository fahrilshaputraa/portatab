"""Tenants, branches, tenant settings and the audit trail.

A tenant is one subscribed business (docs/BUSINESS-RULES.md §1). Branches belong
to exactly one tenant. Subscription status is deliberately absent here — it lives
in the ``subscriptions`` app and is a separate concept from operational status.
"""

from django.db import models

from apps.core.models import BaseModel


class TenantStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    SUSPENDED = "SUSPENDED", "Ditangguhkan"
    DISABLED = "DISABLED", "Dinonaktifkan"


class BranchStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    INACTIVE = "INACTIVE", "Nonaktif"
    DISABLED = "DISABLED", "Dinonaktifkan"


class Tenant(BaseModel):
    """One subscribed F&B business."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=64, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    status = models.CharField(
        max_length=16, choices=TenantStatus.choices, default=TenantStatus.ACTIVE, db_index=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def is_operational(self) -> bool:
        return self.status == TenantStatus.ACTIVE


class Branch(BaseModel):
    """A physical location belonging to one tenant."""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    timezone = models.CharField(max_length=64, default="Asia/Jakarta")
    status = models.CharField(
        max_length=16, choices=BranchStatus.choices, default=BranchStatus.ACTIVE, db_index=True
    )
    accepts_orders = models.BooleanField(
        default=True,
        help_text="Kalau dimatikan, cabang tidak menerima checkout baru (order lama tetap selesai).",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_branch_tenant_code"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def can_accept_orders(self) -> bool:
        return (
            self.status == BranchStatus.ACTIVE
            and self.accepts_orders
            and self.tenant.is_operational
        )


class TenantSettings(BaseModel):
    """Flexible per-tenant configuration (business policy, notifications, ...).

    Stored as key/value rows so new settings need no migration, mirroring the
    ``tenant_settings`` entity in docs/ERD.md.
    """

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="settings")
    setting_key = models.CharField(max_length=128)
    setting_value = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["tenant_id", "setting_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "setting_key"], name="uniq_tenant_setting_key"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.setting_key}"


class AuditLog(models.Model):
    """Immutable record of sensitive actions (docs/BUSINESS-RULES.md §17)."""

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=64)
    entity_type = models.CharField(max_length=64, blank=True)
    entity_id = models.UUIDField(null=True, blank=True)
    before_data = models.JSONField(null=True, blank=True)
    after_data = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} [{self.entity_type}:{self.entity_id}]"
