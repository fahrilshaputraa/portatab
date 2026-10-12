"""Platform-level administration.

Platform admins are separate from tenant owners (docs/BUSINESS-RULES.md §2) and
are never automatically owners of a tenant.
"""

from django.db import models

from apps.core.models import UUIDModel


class PlatformAdminStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    SUSPENDED = "SUSPENDED", "Ditangguhkan"


class PlatformAdminRole(UUIDModel):
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class PlatformAdminMembership(UUIDModel):
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="platform_admin_memberships"
    )
    role = models.ForeignKey(
        PlatformAdminRole, on_delete=models.PROTECT, related_name="memberships"
    )
    status = models.CharField(
        max_length=16, choices=PlatformAdminStatus.choices, default=PlatformAdminStatus.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"], name="uniq_platform_admin_membership"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.role.code}"
