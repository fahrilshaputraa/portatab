"""Resolves the active tenant/branch for the current request.

This middleware only *resolves* context. It is not an authorization boundary:
every protected view still validates tenant membership and branch access itself
(docs/ARCHITECTURE.md §8). Resolving here keeps that check convenient and
consistent instead of re-reading the session in every view.
"""

from apps.accounts.models import Membership, MembershipStatus

SESSION_TENANT_KEY = "active_tenant_id"
SESSION_BRANCH_KEY = "active_branch_id"


class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        request.membership = None
        request.branch = None

        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            self._resolve(request, user)

        return self.get_response(request)

    def _resolve(self, request, user):
        tenant_id = request.session.get(SESSION_TENANT_KEY)
        memberships = (
            Membership.objects.select_related("tenant", "role")
            .filter(user=user, status=MembershipStatus.ACTIVE)
            .order_by("tenant__name")
        )
        if tenant_id:
            membership = memberships.filter(tenant_id=tenant_id).first()
        else:
            membership = memberships.first()
            if membership is not None:
                request.session[SESSION_TENANT_KEY] = str(membership.tenant_id)

        if membership is None:
            # Stale session pointer (membership revoked) — clear it.
            request.session.pop(SESSION_TENANT_KEY, None)
            request.session.pop(SESSION_BRANCH_KEY, None)
            return

        request.membership = membership
        request.tenant = membership.tenant
        self._resolve_branch(request, membership)

    def _resolve_branch(self, request, membership):
        from apps.tenants.selectors import accessible_branches

        branch_id = request.session.get(SESSION_BRANCH_KEY)
        branches = accessible_branches(membership)
        if branch_id:
            branch = branches.filter(id=branch_id).first()
        else:
            branch = branches.first()
        if branch is not None:
            request.branch = branch
            request.session[SESSION_BRANCH_KEY] = str(branch.id)
        else:
            request.session.pop(SESSION_BRANCH_KEY, None)
