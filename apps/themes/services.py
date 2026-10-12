"""Menu appearance services.

Drafts are kept separate from what customers see: editing never changes the live
theme, and publishing writes an immutable, versioned publication
(docs/BUSINESS-RULES.md §14). Template choice is limited by the tenant's plan.
"""

from __future__ import annotations

import re

from django.db import transaction
from django.db.models import Max

from apps.subscriptions.services import active_plan
from apps.themes.models import (
    PublicationStatus,
    TenantTheme,
    TenantThemeStatus,
    ThemeAuditLog,
    ThemePublication,
    ThemeTemplate,
    ThemeTemplateStatus,
)

HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
LAYOUTS = {"grid", "list"}

# Plan order used to decide which templates a tenant may pick.
PLAN_ORDER = {"STARTER": 1, "GROWTH": 2, "BUSINESS": 3}

DEFAULT_CONFIG = {
    "logo_url": "",
    "banner_url": "",
    "primary_color": "#0068f9",
    "layout": "list",
}

# Minimum contrast between the accent colour and white button text.
MIN_CONTRAST = 3.0


class ThemeError(Exception):
    """Raised when a theme configuration cannot be saved or published."""


# ------------------------------------------------------- colour maths -------


def _channel(value: int) -> float:
    ratio = value / 255
    return ratio / 12.92 if ratio <= 0.04045 else ((ratio + 0.055) / 1.055) ** 2.4


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(char * 2 for char in value)
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def relative_luminance(hex_color: str) -> float:
    red, green, blue = _rgb(hex_color)
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(first: str, second: str) -> float:
    """WCAG contrast ratio between two hex colours (1.0 – 21.0)."""
    light, dark = sorted(
        (relative_luminance(first), relative_luminance(second)), reverse=True
    )
    return (light + 0.05) / (dark + 0.05)


def validate_config(config: dict) -> list[str]:
    """Return human-readable problems; an empty list means the config is usable."""
    problems: list[str] = []

    primary = str(config.get("primary_color") or "").strip()
    if not HEX_RE.match(primary):
        problems.append("Warna utama harus berupa kode HEX, misalnya #0068f9.")
    elif contrast_ratio(primary, "#ffffff") < MIN_CONTRAST:
        problems.append(
            "Warna utama terlalu terang: kontras terhadap teks putih kurang dari "
            f"{MIN_CONTRAST}:1, tombol akan sulit dibaca."
        )

    layout = config.get("layout")
    if layout not in LAYOUTS:
        problems.append("Tata letak harus 'grid' atau 'list'.")

    return problems


# ------------------------------------------------------------ templates -----


def _plan_rank(tenant) -> int:
    plan = active_plan(tenant)
    return PLAN_ORDER.get(plan.code if plan else "", 0)


def available_templates(tenant):
    """Templates the tenant's plan allows, cheap plans first."""
    rank = _plan_rank(tenant)
    templates = ThemeTemplate.objects.filter(status=ThemeTemplateStatus.ACTIVE)
    return [item for item in templates if PLAN_ORDER.get(item.minimum_plan, 0) <= rank]


def assert_template_allowed(*, tenant, template) -> None:
    if template.status != ThemeTemplateStatus.ACTIVE:
        raise ThemeError("Template ini sedang tidak tersedia.")
    if PLAN_ORDER.get(template.minimum_plan, 0) > _plan_rank(tenant):
        raise ThemeError("Paket Anda belum mencakup template ini.")


def ensure_theme(tenant) -> TenantTheme:
    """Every tenant has one theme row; create it from the cheapest template."""
    existing = TenantTheme.objects.filter(tenant=tenant).select_related("template").first()
    if existing is not None:
        return existing
    templates = available_templates(tenant)
    if not templates:
        raise ThemeError("Belum ada template yang tersedia untuk paket Anda.")
    template = templates[0]
    return TenantTheme.objects.create(
        tenant=tenant,
        template=template,
        draft_configuration={**DEFAULT_CONFIG, **template.default_configuration},
    )


# ------------------------------------------------------- draft / publish ----


def save_draft(*, tenant_theme, config: dict, actor=None) -> TenantTheme:
    """Validate and store a draft. The live menu is untouched."""
    problems = validate_config(config)
    if problems:
        raise ThemeError(" ".join(problems))
    tenant_theme.draft_configuration = config
    tenant_theme.status = TenantThemeStatus.DRAFT
    tenant_theme.save(update_fields=["draft_configuration", "status", "updated_at"])
    ThemeAuditLog.objects.create(
        tenant_theme=tenant_theme, action="theme.draft_saved", actor=actor, payload=config
    )
    return tenant_theme


@transaction.atomic
def publish(*, tenant_theme, actor=None) -> ThemePublication:
    """Freeze the current draft into a new publication version."""
    problems = validate_config(tenant_theme.draft_configuration or {})
    if problems:
        raise ThemeError(" ".join(problems))

    latest = tenant_theme.publications.aggregate(top=Max("version_number"))["top"] or 0
    tenant_theme.publications.filter(status=PublicationStatus.PUBLISHED).update(
        status=PublicationStatus.SUPERSEDED
    )
    publication = ThemePublication.objects.create(
        tenant_theme=tenant_theme,
        version_number=latest + 1,
        published_configuration=tenant_theme.draft_configuration,
        status=PublicationStatus.PUBLISHED,
    )
    tenant_theme.status = TenantThemeStatus.PUBLISHED
    tenant_theme.save(update_fields=["status", "updated_at"])
    ThemeAuditLog.objects.create(
        tenant_theme=tenant_theme,
        action="theme.published",
        actor=actor,
        payload={"version": publication.version_number},
    )
    return publication


def current_publication(tenant) -> ThemePublication | None:
    theme = TenantTheme.objects.filter(tenant=tenant).first()
    if theme is None:
        return None
    return (
        theme.publications.filter(status=PublicationStatus.PUBLISHED)
        .order_by("-version_number")
        .first()
    )


def live_config(tenant) -> dict:
    """The configuration customers actually see, falling back to defaults."""
    publication = current_publication(tenant)
    if publication is None:
        return dict(DEFAULT_CONFIG)
    return {**DEFAULT_CONFIG, **(publication.published_configuration or {})}
