"""Tenant/branch services plus the audit-trail writer.

``record_audit`` is the only place that writes ``AuditLog`` rows so every
sensitive action is recorded the same way (docs/BUSINESS-RULES.md §17).
"""

from django.db import transaction
from django.utils.text import slugify

from apps.accounts.roles import RoleCode
from apps.accounts.services import create_membership, seed_system_roles
from apps.tenants.models import AuditLog, Branch, Tenant


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
