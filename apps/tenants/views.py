"""Owner/staff portal views: dashboard and workspace switching."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import Membership, MembershipStatus
from apps.accounts.roles import Perm
from apps.orders.selectors import kitchen_queue, pending_orders
from apps.reports.selectors import sales_summary
from apps.subscriptions.services import SubscriptionError, assert_can_add_branch
from apps.tenants.forms import BranchForm, BusinessProfileForm, OperationalPolicyForm
from apps.tenants.models import Branch
from apps.tenants.permissions import require_permission, require_tenant
from apps.tenants.selectors import accessible_branches
from apps.tenants.services import (
    SETTING_CASH_ORDERS_TO_KITCHEN,
    SETTING_LOW_STOCK_THRESHOLD,
    cash_orders_to_kitchen,
    low_stock_threshold,
    record_audit,
    set_setting,
)


@login_required
@require_tenant
def dashboard(request):
    branch = request.branch
    today = timezone.localdate()

    summary = sales_summary(branch=branch, start=today, end=today) if branch else None
    context = {
        "summary": summary,
        "pending_count": pending_orders(branch=branch).count() if branch else 0,
        "kitchen_count": (
            kitchen_queue(
                branch=branch,
                allow_cash_before_payment=cash_orders_to_kitchen(request.tenant),
            ).count()
            if branch
            else 0
        ),
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


@login_required
@require_tenant
@require_permission(Perm.SETTINGS_MANAGE)
def business_settings(request):
    """Business profile, per-branch configuration and operational policy."""
    tenant = request.tenant
    profile_form = BusinessProfileForm(instance=tenant)
    policy_form = OperationalPolicyForm(
        initial={
            "cash_orders_to_kitchen": cash_orders_to_kitchen(tenant),
            "low_stock_threshold": low_stock_threshold(tenant),
        }
    )

    if request.method == "POST":
        section = request.POST.get("section")

        if section == "profile":
            profile_form = BusinessProfileForm(request.POST, instance=tenant)
            if profile_form.is_valid():
                profile_form.save()
                record_audit(
                    action="tenant.profile_updated",
                    tenant=tenant,
                    user=request.user,
                    entity=tenant,
                    request=request,
                )
                messages.success(request, "Profil bisnis disimpan.")
                return redirect("tenants:settings")

        elif section == "policy":
            policy_form = OperationalPolicyForm(request.POST)
            if policy_form.is_valid():
                set_setting(
                    tenant,
                    SETTING_CASH_ORDERS_TO_KITCHEN,
                    bool(policy_form.cleaned_data["cash_orders_to_kitchen"]),
                )
                set_setting(
                    tenant,
                    SETTING_LOW_STOCK_THRESHOLD,
                    int(policy_form.cleaned_data["low_stock_threshold"]),
                )
                record_audit(
                    action="tenant.policy_updated",
                    tenant=tenant,
                    user=request.user,
                    entity=tenant,
                    request=request,
                )
                messages.success(request, "Kebijakan operasional disimpan.")
                return redirect("tenants:settings")

    return render(
        request,
        "tenants/settings/business.html",
        {
            "profile_form": profile_form,
            "policy_form": policy_form,
            "branches": Branch.objects.filter(tenant=tenant).order_by("name"),
        },
    )


@login_required
@require_tenant
@require_permission(Perm.SETTINGS_MANAGE)
def branch_form(request, pk=None):
    branch = get_object_or_404(Branch, pk=pk, tenant=request.tenant) if pk else None

    if request.method == "POST":
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            if branch is None:
                try:
                    assert_can_add_branch(request.tenant)
                except SubscriptionError as exc:
                    messages.error(request, str(exc))
                    return render(
                        request,
                        "tenants/settings/branch_form.html",
                        {"form": form, "branch": branch},
                    )
            obj = form.save(commit=False)
            obj.tenant = request.tenant
            obj.save()
            record_audit(
                action="branch.saved",
                tenant=request.tenant,
                user=request.user,
                entity=obj,
                request=request,
            )
            messages.success(request, "Cabang disimpan.")
            return redirect("tenants:settings")
    else:
        form = BranchForm(instance=branch)

    return render(
        request, "tenants/settings/branch_form.html", {"form": form, "branch": branch}
    )


@login_required
@require_tenant
@require_permission(Perm.SETTINGS_MANAGE)
@require_POST
def branch_toggle_orders(request, pk):
    """Pause or resume order acceptance for one branch without editing the form."""
    branch = get_object_or_404(Branch, pk=pk, tenant=request.tenant)
    branch.accepts_orders = not branch.accepts_orders
    branch.save(update_fields=["accepts_orders", "updated_at"])
    record_audit(
        action="branch.order_acceptance_changed",
        tenant=request.tenant,
        user=request.user,
        entity=branch,
        after={"accepts_orders": branch.accepts_orders},
        request=request,
    )
    state = "menerima" if branch.accepts_orders else "berhenti menerima"
    messages.success(request, f"{branch.name} {state} order baru.")
    return redirect("tenants:settings")
