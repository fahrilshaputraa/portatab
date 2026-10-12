"""Menu appearance: templates, tenant drafts, publications and media.

Drafts are stored separately from the published configuration so editing never
changes what customers currently see (docs/BUSINESS-RULES.md §14). Templates are
controlled application code — tenant input is validated and escaped, never
executed.
"""

from django.db import models

from apps.core.models import BaseModel, UUIDModel


class ThemeTemplateStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    INACTIVE = "INACTIVE", "Nonaktif"


class TenantThemeStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Dipublikasikan"


class PublicationStatus(models.TextChoices):
    PUBLISHED = "PUBLISHED", "Dipublikasikan"
    SUPERSEDED = "SUPERSEDED", "Digantikan"


class ThemeTemplate(BaseModel):
    """A controlled menu template registered by the platform."""

    template_key = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    version = models.CharField(max_length=32, default="1.0.0")
    minimum_plan = models.CharField(
        max_length=32, blank=True, help_text="Kode plan minimum yang boleh memakai template ini."
    )
    status = models.CharField(
        max_length=16, choices=ThemeTemplateStatus.choices, default=ThemeTemplateStatus.ACTIVE
    )
    default_configuration = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class TenantTheme(BaseModel):
    """A tenant's theme, pointing at a template with its current draft config."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="themes"
    )
    template = models.ForeignKey(
        ThemeTemplate, on_delete=models.PROTECT, related_name="tenant_themes"
    )
    draft_configuration = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16, choices=TenantThemeStatus.choices, default=TenantThemeStatus.DRAFT
    )

    class Meta:
        ordering = ["tenant_id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant"], name="uniq_tenant_theme"),
        ]

    def __str__(self) -> str:
        return f"{self.tenant_id}@{self.template.template_key}"


class ThemePublication(UUIDModel):
    """A traceable published version of a tenant theme."""

    tenant_theme = models.ForeignKey(
        TenantTheme, on_delete=models.CASCADE, related_name="publications"
    )
    version_number = models.PositiveIntegerField()
    published_configuration = models.JSONField()
    status = models.CharField(
        max_length=16, choices=PublicationStatus.choices, default=PublicationStatus.PUBLISHED
    )
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_theme", "version_number"], name="uniq_theme_publication_version"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.tenant_theme_id} v{self.version_number}"


class MediaAsset(UUIDModel):
    """A tenant-owned uploaded file (logo, banner, product photo)."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="media_assets"
    )
    file_url = models.URLField()
    media_type = models.CharField(max_length=32, default="image")
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.original_filename or self.file_url


class ThemeAuditLog(UUIDModel):
    """Records theme draft/publish actions (docs/PRD.md §16.7)."""

    tenant_theme = models.ForeignKey(
        TenantTheme, on_delete=models.CASCADE, related_name="audit_logs"
    )
    actor = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    action = models.CharField(max_length=64)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.action} @ {self.tenant_theme_id}"
