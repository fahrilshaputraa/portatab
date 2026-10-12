"""Owner-facing subscription and billing overview."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.roles import Perm
from apps.subscriptions import services
from apps.subscriptions.forms import SubscribeForm
from apps.subscriptions.models import Plan, PlanStatus, SubscriptionInvoice
from apps.tenants.permissions import require_permission, require_tenant
from apps.tenants.services import record_audit


@login_required
@require_tenant
@require_permission(Perm.SUBSCRIPTION_MANAGE)
def overview(request):
    tenant = request.tenant
    subscription = services.current_subscription(tenant)

    if request.method == "POST":
        form = SubscribeForm(request.POST)
        if form.is_valid():
            try:
                subscription, invoice = services.subscribe(
                    tenant=tenant,
                    plan=form.cleaned_data["plan"],
                    voucher_code=form.cleaned_data["voucher_code"],
                    actor=request.user,
                )
            except services.SubscriptionError as exc:
                messages.error(request, str(exc))
            else:
                record_audit(
                    action="subscription.activated",
                    tenant=tenant,
                    user=request.user,
                    entity=subscription,
                    after={"plan": subscription.plan.code, "invoice": invoice.invoice_number},
                    request=request,
                )
                messages.success(
                    request,
                    f"Paket {subscription.plan.name} aktif. Invoice {invoice.invoice_number} diterbitkan.",
                )
                return redirect("subscriptions:overview")
    else:
        form = SubscribeForm(
            initial={"plan": subscription.plan_id if subscription else None}
        )

    invoices = (
        SubscriptionInvoice.objects.filter(subscription__tenant=tenant)
        .select_related("subscription", "subscription__plan")
        .order_by("-created_at")[:20]
    )

    return render(
        request,
        "subscriptions/overview.html",
        {
            "subscription": subscription,
            "form": form,
            "invoices": invoices,
            "usage": services.usage(tenant),
            "plans": Plan.objects.filter(status=PlanStatus.ACTIVE).order_by("monthly_price"),
        },
    )
