"""Tenant/branch authorization primitives.

Views use these helpers so authorization is enforced the same way everywhere and
is never left to the frontend (docs/AGENTS.md §6, docs/BUSINESS-RULES.md §2).
"""

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect

from apps.platform_admin.permissions import is_platform_admin

NO_TENANT_MESSAGE = "Tidak ada konteks tenant aktif untuk akun ini."


def _no_tenant_context(request):
    """Refuse a tenant view for a user with no active tenant context.

    A platform admin is not a tenant member (docs/BUSINESS-RULES.md §2), so the
    business portal is a dead end for them: they are sent to the platform console
    they do own. Everyone else is denied, exactly as before.
    """
    if is_platform_admin(request.user):
        return redirect("platform_console:home")
    raise PermissionDenied(NO_TENANT_MESSAGE)


def require_tenant(view):
    """Require an active tenant context (resolved by TenantContextMiddleware)."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if getattr(request, "membership", None) is None:
            return _no_tenant_context(request)
        return view(request, *args, **kwargs)

    return wrapper


def require_permission(code: str):
    """Require the active membership's role to grant ``code``."""

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            membership = getattr(request, "membership", None)
            if membership is None:
                return _no_tenant_context(request)
            if not membership.has_permission(code):
                raise PermissionDenied("Anda tidak memiliki izin untuk aksi ini.")
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def get_tenant_object_or_404(model, membership, **lookup):
    """Fetch a tenant-scoped object, 404ing on cross-tenant access.

    Returns 404 (not 403) so existence in another tenant is never revealed
    (docs/API-CONVENTIONS.md §5.4).
    """
    try:
        return model.objects.get(tenant_id=membership.tenant_id, **lookup)
    except model.DoesNotExist as exc:
        raise Http404("Objek tidak ditemukan.") from exc


def get_branch_object_or_404(model, branch, **lookup):
    """Fetch a branch-scoped object, 404ing on cross-branch access."""
    try:
        return model.objects.get(branch_id=branch.id, **lookup)
    except model.DoesNotExist as exc:
        raise Http404("Objek tidak ditemukan.") from exc
