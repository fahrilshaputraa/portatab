"""Template context shared by every page that renders inside a tenant."""

from apps.tenants.selectors import accessible_branches


def tenant_context(request):
    tenant = getattr(request, "tenant", None)
    membership = getattr(request, "membership", None)
    return {
        "current_tenant": tenant,
        "current_membership": membership,
        "current_branch": getattr(request, "branch", None),
        "accessible_branches": accessible_branches(membership) if membership else [],
    }
