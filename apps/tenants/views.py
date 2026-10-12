"""Owner/staff portal views: dashboard and workspace switching."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.models import Membership, MembershipStatus
from apps.orders.selectors import kitchen_queue, pending_orders
from apps.reports.selectors import sales_summary
from apps.tenants.permissions import require_tenant
from apps.tenants.selectors import accessible_branches


@login_required
@require_tenant
def dashboard(request):
    branch = request.branch
    today = timezone.localdate()

    summary = sales_summary(branch=branch, start=today, end=today) if branch else None
    context = {
        "summary": summary,
        "pending_count": pending_orders(branch=branch).count() if branch else 0,
        "kitchen_count": kitchen_queue(branch=branch).count() if branch else 0,
    }
    return render(request, "tenants/dashboard/dashboard.html", context)


@login_required
def switch_workspace(request):
    """Change the active tenant/branch, validating membership first."""
    if request.method != "POST":
        return redirect("tenants:dashboard")

    tenant_id = request.POST.get("tenant")
    branch_id = request.POST.get("branch")

    membership = Membership.objects.filter(
        user=request.user, tenant_id=tenant_id, status=MembershipStatus.ACTIVE
    ).first()
    if membership is None:
        messages.error(request, "Anda tidak punya akses ke workspace tersebut.")
        return redirect("tenants:dashboard")

    request.session["active_tenant_id"] = str(membership.tenant_id)
    request.session.pop("active_branch_id", None)
    if branch_id and accessible_branches(membership).filter(id=branch_id).exists():
        request.session["active_branch_id"] = branch_id
    messages.success(request, "Workspace diganti.")
    return redirect("tenants:dashboard")
