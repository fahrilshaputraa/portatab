"""Menu management views (categories, products, branch pricing).

Actions are permission-checked and tenant-scoped. Ordinary navigation renders full
pages; the product list supports an HTMX search fragment.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.roles import Perm
from apps.catalog.forms import (
    BranchProductForm,
    CategoryForm,
    ProductForm,
    ProductVariantFormSet,
)
from apps.catalog.models import BranchProduct, Category, Product
from apps.tenants.permissions import require_permission, require_tenant


@login_required
@require_tenant
@require_permission(Perm.CATALOG_VIEW)
def product_list(request):
    query = request.GET.get("q", "").strip()
    products = (
        Product.objects.filter(tenant=request.tenant)
        .select_related("category")
        .annotate(variant_count=Count("variants"))
    )
    if query:
        products = products.filter(Q(name__icontains=query) | Q(category__name__icontains=query))

    context = {"products": products, "query": query}
    if request.headers.get("HX-Request"):
        return render(request, "catalog/products/_table.html", context)
    return render(request, "catalog/products/list.html", context)


@login_required
@require_tenant
@require_permission(Perm.CATALOG_MANAGE)
def product_form(request, pk=None):
    product = None
    if pk is not None:
        product = get_object_or_404(Product, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product, tenant=request.tenant)
        formset = ProductVariantFormSet(request.POST, instance=product or Product(tenant=request.tenant))
        if form.is_valid() and formset.is_valid():
            product = form.save(commit=False)
            product.tenant = request.tenant
            product.save()
            formset.instance = product
            formset.save()
            messages.success(request, "Produk disimpan.")
            return redirect("catalog_products:list")
    else:
        form = ProductForm(instance=product, tenant=request.tenant)
        formset = ProductVariantFormSet(instance=product or Product(tenant=request.tenant))

    return render(
        request,
        "catalog/products/form.html",
        {"form": form, "formset": formset, "product": product},
    )


@login_required
@require_tenant
@require_permission(Perm.CATALOG_MANAGE)
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, tenant=request.tenant)
    if request.method == "POST":
        product.status = "INACTIVE"
        product.save(update_fields=["status", "updated_at"])
        messages.success(request, "Produk dinonaktifkan.")
    return redirect("catalog_products:list")


@login_required
@require_tenant
@require_permission(Perm.CATALOG_MANAGE)
def branch_pricing(request, pk):
    """Configure the product's price/availability/stock at the active branch."""
    product = get_object_or_404(Product, pk=pk, tenant=request.tenant)
    if request.branch is None:
        messages.error(request, "Pilih cabang terlebih dahulu.")
        return redirect("catalog_products:list")

    branch_product, _ = BranchProduct.objects.get_or_create(
        branch=request.branch, product=product, defaults={"price": 0}
    )

    if request.method == "POST":
        form = BranchProductForm(request.POST, instance=branch_product)
        if form.is_valid():
            form.save()
            messages.success(request, "Konfigurasi cabang disimpan.")
            return redirect("catalog_products:list")
    else:
        form = BranchProductForm(instance=branch_product)

    return render(
        request,
        "catalog/products/branch_form.html",
        {"form": form, "product": product, "branch_product": branch_product},
    )


@login_required
@require_tenant
@require_permission(Perm.CATALOG_VIEW)
def category_list(request):
    categories = Category.objects.filter(tenant=request.tenant)
    return render(request, "catalog/categories/list.html", {"categories": categories})


@login_required
@require_tenant
@require_permission(Perm.CATALOG_MANAGE)
def category_form(request, pk=None):
    category = None
    if pk is not None:
        category = get_object_or_404(Category, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category.tenant = request.tenant
            category.save()
            messages.success(request, "Kategori disimpan.")
            return redirect("catalog_categories:list")
    else:
        form = CategoryForm(instance=category)

    return render(request, "catalog/categories/form.html", {"form": form, "category": category})


@login_required
@require_tenant
@require_permission(Perm.CATALOG_MANAGE)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, tenant=request.tenant)
    if request.method == "POST":
        category.is_active = False
        category.save(update_fields=["is_active", "updated_at"])
        messages.success(request, "Kategori dinonaktifkan.")
    return redirect("catalog_categories:list")
