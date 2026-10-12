"""Sales reporting views with CSV export."""

import csv
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.roles import Perm
from apps.reports import selectors
from apps.tenants.permissions import require_permission, require_tenant


def _parse_range(request) -> tuple:
    today = timezone.localdate()
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")
    try:
        start = datetime.strptime(start_raw, "%Y-%m-%d").date() if start_raw else today
    except ValueError:
        start = today
    try:
        end = datetime.strptime(end_raw, "%Y-%m-%d").date() if end_raw else today
    except ValueError:
        end = today
    if end < start:
        start, end = end, start
    return start, end


def _scope(request) -> dict:
    """Branch when one is active, otherwise the whole tenant."""
    if request.branch is not None:
        return {"branch": request.branch}
    return {"tenant": request.tenant}


@login_required
@require_tenant
@require_permission(Perm.REPORTS_VIEW)
def sales(request):
    start, end = _parse_range(request)
    scope = _scope(request)
    context = {
        "start": start,
        "end": end,
        "summary": selectors.sales_summary(start=start, end=end, **scope),
        "top_products": selectors.top_products(start=start, end=end, **scope),
        "methods": selectors.payment_method_breakdown(start=start, end=end, **scope),
    }
    if request.headers.get("HX-Request"):
        return render(request, "reports/_report.html", context)
    return render(request, "reports/sales.html", context)


@login_required
@require_tenant
@require_permission(Perm.REPORTS_VIEW)
def sales_csv(request):
    start, end = _parse_range(request)
    scope = _scope(request)
    summary = selectors.sales_summary(start=start, end=end, **scope)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="laporan-{start}-{end}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(["Metrik", "Nilai"])
    writer.writerow(["Periode", f"{start} s/d {end}"])
    writer.writerow(["Order selesai", summary["order_count"]])
    writer.writerow(["Penjualan kotor", summary["gross_sales"]])
    writer.writerow(["Diskon", summary["discounts"]])
    writer.writerow(["Penjualan bersih", summary["net_sales"]])
    writer.writerow(["Dibayar", summary["paid_amount"]])
    writer.writerow(["Belum dibayar", summary["unpaid_amount"]])
    writer.writerow(["Refund berhasil", summary["refunded_amount"]])
    writer.writerow(["Bersih setelah refund", summary["net_after_refund"]])
    writer.writerow(["Order dibatalkan/ditolak", summary["cancelled_count"]])
    return response
