"""Cashier and kitchen portal views.

Status changes go through ``orders.services`` so the state machine and its
side-effects (stock, notifications, audit) always run. HTMX actions return the
refreshed order row.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from apps.accounts.roles import Perm
from apps.orders import services
from apps.orders.forms import RejectOrderForm
from apps.orders.models import Order
from apps.orders.selectors import cashier_queue, kitchen_queue, pending_orders
from apps.tenants.permissions import require_permission, require_tenant
from apps.tenants.services import cash_orders_to_kitchen


def _render_row(request, order, *, template: str, error: str = "", status: int = 200):
    return render(request, template, {"order": order, "row_error": error}, status=status)


def _run_action(request, pk, action, *, template: str, payload=None):
    """Run an order action and return the refreshed row (or a 400 with the reason)."""
    order = get_object_or_404(Order, pk=pk, branch=request.branch)
    try:
        action(order=order, actor=request.user, **(payload or {}))
    except services.OrderError as exc:
        order.refresh_from_db()
        return _render_row(request, order, template=template, error=str(exc), status=400)
    order.refresh_from_db()
    return _render_row(request, order, template=template)


@login_required
@require_tenant
@require_permission(Perm.ORDERS_VIEW)
def cashier(request):
    if request.branch is not None:
        # Server-side clock is authoritative for the 3/5-minute timers.
        services.evaluate_pending_orders(branch=request.branch)
        orders = cashier_queue(branch=request.branch)
        pending = pending_orders(branch=request.branch)
    else:
        orders = Order.objects.none()
        pending = Order.objects.none()

    context = {"orders": orders, "pending": pending, "reject_form": RejectOrderForm()}
    if request.headers.get("HX-Request"):
        return render(request, "orders/cashier/_list.html", context)
    return render(request, "orders/cashier/index.html", context)


@login_required
@require_tenant
@require_permission(Perm.ORDERS_VIEW)
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related("branch", "table", "customer").prefetch_related(
            "items", "status_history", "payments"
        ),
        pk=pk,
        branch=request.branch,
    )
    return render(request, "orders/detail.html", {"order": order})


@login_required
@require_tenant
@require_permission(Perm.ORDERS_ACCEPT)
@require_http_methods(["POST"])
def accept_order(request, pk):
    return _run_action(request, pk, services.accept_order, template="orders/_cashier_row.html")


@login_required
@require_tenant
@require_permission(Perm.ORDERS_REJECT)
@require_http_methods(["POST"])
def reject_order(request, pk):
    form = RejectOrderForm(request.POST)
    reason = form.cleaned_data.get("reason", "") if form.is_valid() else ""
    return _run_action(
        request,
        pk,
        services.reject_order,
        template="orders/_cashier_row.html",
        payload={"reason": reason},
    )


@login_required
@require_tenant
@require_permission(Perm.ORDERS_COMPLETE)
@require_http_methods(["POST"])
def complete_order(request, pk):
    return _run_action(
        request, pk, services.complete_order, template="orders/_cashier_row.html"
    )


@login_required
@require_tenant
@require_permission(Perm.ORDERS_VIEW)
def kitchen(request):
    if request.branch is not None:
        orders = kitchen_queue(
            branch=request.branch,
            allow_cash_before_payment=cash_orders_to_kitchen(request.tenant),
        )
    else:
        orders = Order.objects.none()
    return render(request, "orders/kitchen/index.html", {"orders": orders})


@login_required
@require_tenant
@require_permission(Perm.ORDERS_PREPARE)
@require_http_methods(["POST"])
def start_preparing(request, pk):
    return _run_action(
        request, pk, services.start_preparing, template="orders/kitchen/_kitchen_card.html"
    )


@login_required
@require_tenant
@require_permission(Perm.ORDERS_READY)
@require_http_methods(["POST"])
def mark_ready(request, pk):
    return _run_action(
        request, pk, services.mark_ready, template="orders/kitchen/_kitchen_card.html"
    )


@login_required
@require_tenant
@require_permission(Perm.ORDERS_VIEW)
def kitchen_board(request):
    """Compact polling endpoint that returns only orders still in the kitchen queue."""
    orders = (
        kitchen_queue(
            branch=request.branch,
            allow_cash_before_payment=cash_orders_to_kitchen(request.tenant),
        )
        if request.branch
        else Order.objects.none()
    )
    return render(request, "orders/kitchen/_board.html", {"orders": orders})
