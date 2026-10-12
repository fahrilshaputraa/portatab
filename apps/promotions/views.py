"""Promotion management views (owner-facing)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.roles import Perm
from apps.promotions.forms import PromotionForm
from apps.promotions.models import Promotion, RedemptionStatus
from apps.tenants.permissions import require_permission, require_tenant
from apps.tenants.services import record_audit


@login_required
@require_tenant
@require_permission(Perm.PROMOTIONS_VIEW)
def promotion_list(request):
    promotions = (
        Promotion.objects.filter(tenant=request.tenant)
        .annotate(
            redeemed_count=Count(
                "redemptions",
                filter=Q(redemptions__status=RedemptionStatus.APPLIED),
            )
        )
        .order_by("-created_at")
    )
    return render(request, "promotions/list.html", {"promotions": promotions})


@login_required
@require_tenant
@require_permission(Perm.PROMOTIONS_MANAGE)
def promotion_form(request, pk=None):
    promotion = get_object_or_404(Promotion, pk=pk, tenant=request.tenant) if pk else None

    if request.method == "POST":
        form = PromotionForm(request.POST, instance=promotion, tenant=request.tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.tenant
            obj.save()
            form.save_m2m()
            record_audit(
                action="promotion.saved",
                tenant=request.tenant,
                user=request.user,
                entity=obj,
                after={"code": obj.code, "status": obj.status},
                request=request,
            )
            messages.success(request, "Promosi disimpan.")
            return redirect("promotions:list")
    else:
        form = PromotionForm(instance=promotion, tenant=request.tenant)

    return render(request, "promotions/form.html", {"form": form, "promotion": promotion})
