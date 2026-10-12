"""Table and QR management views.

QR tokens only open the public menu; they never grant dashboard access
(docs/PRD.md §9.2).
"""

import io

import qrcode
import qrcode.image.svg
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.roles import Perm
from apps.tables.forms import TableForm
from apps.tables.models import Table
from apps.tenants.permissions import require_permission, require_tenant


def menu_url_for(request, table: Table) -> str:
    return request.build_absolute_uri(reverse("menu:menu", args=[table.qr_token]))


@login_required
@require_tenant
@require_permission(Perm.TABLES_VIEW)
def table_list(request):
    tables = Table.objects.filter(branch=request.branch) if request.branch else Table.objects.none()
    return render(request, "tables/list.html", {"tables": tables})


@login_required
@require_tenant
@require_permission(Perm.TABLES_MANAGE)
def table_form(request, pk=None):
    if request.branch is None:
        messages.error(request, "Pilih cabang terlebih dahulu.")
        return redirect("tables:list")

    table = get_object_or_404(Table, pk=pk, branch=request.branch) if pk else None

    if request.method == "POST":
        form = TableForm(request.POST, instance=table)
        if form.is_valid():
            table = form.save(commit=False)
            table.branch = request.branch
            table.save()
            messages.success(request, "Meja disimpan.")
            return redirect("tables:list")
    else:
        form = TableForm(instance=table)

    return render(request, "tables/form.html", {"form": form, "table": table})


@login_required
@require_tenant
@require_permission(Perm.TABLES_VIEW)
def table_qr(request, pk):
    table = get_object_or_404(Table, pk=pk, branch=request.branch) if request.branch else None
    if table is None:
        messages.error(request, "Meja tidak ditemukan pada cabang aktif.")
        return redirect("tables:list")

    url = menu_url_for(request, table)
    image = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)
    buffer = io.BytesIO()
    image.save(buffer)
    return render(
        request,
        "tables/qr.html",
        {"table": table, "menu_url": url, "qr_svg": buffer.getvalue().decode()},
    )


@login_required
@require_tenant
@require_permission(Perm.TABLES_MANAGE)
def table_rotate_qr(request, pk):
    table = get_object_or_404(Table, pk=pk, branch=request.branch) if request.branch else None
    if table is None or request.method != "POST":
        return redirect("tables:list")
    table.rotate_qr_token()
    messages.success(request, "Token QR diganti. QR lama tidak berlaku lagi.")
    return redirect("tables:qr", pk=table.pk)
