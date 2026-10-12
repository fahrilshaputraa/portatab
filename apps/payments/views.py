"""Payment and refund views (staff portal) and the provider webhook."""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.accounts.roles import Perm
from apps.payments import services
from apps.payments.forms import RefundForm
from apps.payments.models import Payment, Refund
from apps.payments.webhooks import process_midtrans_notification
from apps.tenants.permissions import require_permission, require_tenant

logger = logging.getLogger("portatap.payments")


@login_required
@require_tenant
@require_permission(Perm.PAYMENTS_VIEW)
def payment_list(request):
    if request.branch is not None:
        payments = (
            Payment.objects.filter(order__branch=request.branch)
            .select_related("order")
            .order_by("-created_at")[:100]
        )
        refunds = (
            Refund.objects.filter(payment__order__branch=request.branch)
            .select_related("payment", "payment__order")
            .order_by("-created_at")[:100]
        )
    else:
        payments = Payment.objects.none()
        refunds = Refund.objects.none()
    return render(request, "payments/list.html", {"payments": payments, "refunds": refunds})


@login_required
@require_tenant
@require_permission(Perm.PAYMENTS_CONFIRM_CASH)
@require_POST
def confirm_cash(request, pk):
    payment = get_object_or_404(Payment, pk=pk, order__branch=request.branch)
    try:
        services.confirm_cash_payment(payment=payment, actor=request.user)
    except services.PaymentError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Pembayaran tunai dikonfirmasi.")
    return redirect("orders:detail", pk=payment.order_id)


@login_required
@require_tenant
@require_permission(Perm.PAYMENTS_CONFIRM_CASH)
@require_POST
def initiate_digital(request, pk):
    payment = get_object_or_404(Payment, pk=pk, order__branch=request.branch)
    try:
        result = services.initiate_digital_payment(payment=payment)
    except services.PaymentError as exc:
        messages.error(request, str(exc))
        return redirect("orders:detail", pk=payment.order_id)

    redirect_url = result.get("redirect_url")
    if redirect_url:
        return redirect(redirect_url)
    messages.info(request, "Transaksi digital dibuat. Selesaikan pembayaran.")
    return redirect("orders:detail", pk=payment.order_id)


@login_required
@require_tenant
@require_permission(Perm.REFUNDS_REQUEST)
def refund_create(request, pk):
    payment = get_object_or_404(Payment, pk=pk, order__branch=request.branch)

    if request.method == "POST":
        form = RefundForm(request.POST, payment=payment)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            needs_manager = services.refund_requires_manager_approval(amount)
            if needs_manager and not request.membership.has_permission(Perm.REFUNDS_APPROVE):
                messages.error(
                    request, "Nominal ini melebihi batas kasir dan butuh persetujuan manager."
                )
            else:
                try:
                    services.request_refund(
                        payment=payment,
                        actor=request.user,
                        amount=amount,
                        reason=form.cleaned_data["reason"],
                    )
                except services.PaymentError as exc:
                    messages.error(request, str(exc))
                else:
                    messages.success(request, "Permintaan refund dicatat.")
                    return redirect("orders:detail", pk=payment.order_id)
    else:
        form = RefundForm(payment=payment)

    return render(
        request, "payments/refund_form.html", {"form": form, "payment": payment}
    )


@login_required
@require_tenant
@require_permission(Perm.REFUNDS_APPROVE)
@require_POST
def refund_approve(request, pk):
    refund = get_object_or_404(Refund, pk=pk, payment__order__branch=request.branch)
    try:
        services.approve_refund(refund=refund, actor=request.user)
    except services.PaymentError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Refund disetujui.")
    return redirect("payments:list")


@login_required
@require_tenant
@require_permission(Perm.REFUNDS_REQUEST)
@require_POST
def refund_complete(request, pk):
    refund = get_object_or_404(Refund, pk=pk, payment__order__branch=request.branch)
    try:
        services.complete_refund(refund=refund, actor=request.user)
    except services.PaymentError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Refund diselesaikan.")
    return redirect("payments:list")


@csrf_exempt
@require_POST
def midtrans_webhook(request):
    """Receive a Midtrans notification. Untrusted until the signature verifies."""
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    if not isinstance(payload, dict):
        return HttpResponseBadRequest("Invalid payload")

    try:
        process_midtrans_notification(payload)
    except Exception:  # pragma: no cover - defensive: always ack the provider
        logger.exception("Gagal memproses Webhook Midtrans")
    return HttpResponse("OK")
