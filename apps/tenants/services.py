"""Tenant/branch services plus the audit-trail writer.

``record_audit`` is the only place that writes ``AuditLog`` rows so every
sensitive action is recorded the same way (docs/BUSINESS-RULES.md §17).
"""

from django.db import transaction
from django.utils.text import slugify

from apps.accounts.roles import RoleCode
from apps.accounts.services import create_membership, seed_system_roles
from apps.tenants.models import AuditLog, Branch, Tenant, TenantSettings


def get_client_ip(request) -> str | None:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def record_audit(
    *,
    action: str,
    tenant=None,
    user=None,
    entity=None,
    entity_type: str = "",
    entity_id=None,
    before: dict | None = None,
    after: dict | None = None,
    request=None,
) -> AuditLog:
    """Write one immutable audit row. Never raises for missing optional data."""
    if entity is not None:
        entity_type = entity_type or entity.__class__.__name__
        entity_id = entity_id or getattr(entity, "id", None)

    return AuditLog.objects.create(
        tenant=tenant,
        user=user if (user is not None and getattr(user, "is_authenticated", False)) else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_data=before,
        after_data=after,
        ip_address=get_client_ip(request),
    )


def unique_tenant_slug(name: str) -> str:
    base = slugify(name)[:48] or "tenant"
    slug = base
    index = 1
    while Tenant.objects.filter(slug=slug).exists():
        index += 1
        slug = f"{base}-{index}"
    return slug


@transaction.atomic
def register_business(*, owner, business_name: str, branch_name: str, **tenant_fields) -> tuple:
    """Create a tenant with its first branch and an OWNER membership.

    The single onboarding entry point used by registration and tests
    (docs/PRD.md §7.1).
    """
    tenant = Tenant.objects.create(
        name=business_name, slug=unique_tenant_slug(business_name), **tenant_fields
    )
    seed_system_roles(tenant)
    branch = create_branch(tenant=tenant, name=branch_name, code="MAIN")
    create_membership(tenant=tenant, user=owner, role_code=RoleCode.OWNER, branches=[branch])
    record_audit(action="tenant.created", tenant=tenant, user=owner, entity=tenant)
    return tenant, branch


@transaction.atomic
def create_branch(*, tenant, name: str, code: str, **fields) -> Branch:
    branch = Branch.objects.create(tenant=tenant, name=name, code=code, **fields)
    record_audit(action="branch.created", tenant=tenant, entity=branch)
    return branch


# ---------------------------------------------------------------------------
# Tenant operational settings
#
# Stored as key/value rows so a new policy needs no migration. Defaults live here
# so every reader agrees on the behaviour when a tenant has never configured it.
# ---------------------------------------------------------------------------

SETTING_CASH_ORDERS_TO_KITCHEN = "cash_orders_to_kitchen"
SETTING_LOW_STOCK_THRESHOLD = "low_stock_threshold"

SETTING_DEFAULTS = {
    # A cash order may reach the kitchen before payment when the shop's policy
    # permits it (docs/BUSINESS-RULES.md §8). Default permits — the common
    # warung flow — and owners can turn it off.
    SETTING_CASH_ORDERS_TO_KITCHEN: True,
    SETTING_LOW_STOCK_THRESHOLD: 5,
}


def get_setting(tenant, key: str):
    """Read one tenant setting, falling back to the registered default."""
    if tenant is None:
        return SETTING_DEFAULTS.get(key)
    row = TenantSettings.objects.filter(tenant=tenant, setting_key=key).first()
    if row is None or row.setting_value is None:
        return SETTING_DEFAULTS.get(key)
    value = row.setting_value
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    return value


def set_setting(tenant, key: str, value) -> TenantSettings:
    """Persist one tenant setting."""
    row, _ = TenantSettings.objects.update_or_create(
        tenant=tenant, setting_key=key, defaults={"setting_value": {"value": value}}
    )
    return row


def cash_orders_to_kitchen(tenant) -> bool:
    """Whether a cash order may enter the kitchen before its payment is confirmed."""
    return bool(get_setting(tenant, SETTING_CASH_ORDERS_TO_KITCHEN))


def low_stock_threshold(tenant) -> int:
    """Available stock at or below which a product is flagged as running low."""
    try:
        return int(get_setting(tenant, SETTING_LOW_STOCK_THRESHOLD))
    except (TypeError, ValueError):
        return int(SETTING_DEFAULTS[SETTING_LOW_STOCK_THRESHOLD])
