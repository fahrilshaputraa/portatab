"""Branch stock views: list balances and record corrections."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.roles import Perm
from apps.catalog.models import BranchProduct
from apps.inventory.forms import StockAdjustForm
from apps.inventory.services import InsufficientStock, adjust_stock
from apps.tenants.permissions import require_permission, require_tenant
from apps.tenants.services import low_stock_threshold


@login_required
@require_tenant
@require_permission(Perm.INVENTORY_VIEW)
def inventory_list(request):
    products = (
        BranchProduct.objects.filter(branch=request.branch)
        .select_related("product")
        .order_by("product__name")
        if request.branch
        else BranchProduct.objects.none()
    )
    return render(
        request,
        "inventory/list.html",
        {"products": products, "low_stock_threshold": low_stock_threshold(request.tenant)},
    )


@login_required
@require_tenant
@require_permission(Perm.INVENTORY_MANAGE)
def stock_adjust(request, pk):
    branch_product = (
        get_object_or_404(BranchProduct, pk=pk, branch=request.branch)
        if request.branch
        else None
    )
    if branch_product is None:
        messages.error(request, "Produk tidak ditemukan pada cabang aktif.")
        return redirect("inventory:list")

    if request.method == "POST":
        form = StockAdjustForm(request.POST)
        if form.is_valid():
            try:
                adjust_stock(
                    branch_product=branch_product,
                    quantity_delta=form.cleaned_data["quantity_delta"],
                    actor=request.user,
                    reason=form.cleaned_data["reason"],
                )
            except InsufficientStock as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Stok diperbarui.")
                return redirect("inventory:list")
    else:
        form = StockAdjustForm()

    return render(
        request,
        "inventory/adjust.html",
        {"form": form, "branch_product": branch_product},
    )
