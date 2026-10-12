"""Public customer QR menu.

No account required. Every request is scoped to a valid table QR token and the
backend recalculates prices at checkout (docs/PRD.md §10).
"""

import uuid
from decimal import Decimal

from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.catalog.models import BranchProduct, ProductVariant
from apps.customers.models import Customer
from apps.orders import services
from apps.orders.forms import CheckoutForm
from apps.orders.models import Order, OrderSource
from apps.tables.models import Table


def _get_table(qr_token) -> Table:
    return get_object_or_404(
        Table.objects.select_related("branch", "branch__tenant"), qr_token=qr_token
    )


def _cart_key(qr_token) -> str:
    return f"cart_{qr_token}"


def _load_cart(request, qr_token) -> list[dict]:
    return list(request.session.get(_cart_key(qr_token), []))


def _save_cart(request, qr_token, cart: list[dict]) -> None:
    request.session[_cart_key(qr_token)] = cart


def _invalidate_checkout_key(request, table) -> None:
    """Cart changed, so the next checkout must use a fresh idempotency key."""
    request.session.pop(f"checkout_key_{table.qr_token}", None)


def _cart_lines(request, table) -> tuple[list[dict], Decimal]:
    """Resolve the session cart into priceable lines; drop anything that vanished."""
    cart = _load_cart(request, table.qr_token)
    lines = []
    total = Decimal("0.00")
    changed = False

    for entry in cart:
        branch_product = (
            BranchProduct.objects.filter(
                pk=entry["branch_product_id"], branch=table.branch
            )
            .select_related("product")
            .first()
        )
        if branch_product is None:
            changed = True
            continue
        variant = None
        if entry.get("variant_id"):
            variant = ProductVariant.objects.filter(
                pk=entry["variant_id"], product=branch_product.product
            ).first()
        quantity = int(entry["quantity"])
        unit_price = services.compute_unit_price(branch_product=branch_product, variant=variant)
        subtotal = unit_price * quantity
        total += subtotal
        lines.append(
            {
                "branch_product": branch_product,
                "variant": variant,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
            }
        )

    if changed:
        _save_cart(request, table.qr_token, [])
    return lines, total


def menu(request, qr_token):
    table = _get_table(qr_token)
    products = (
        BranchProduct.objects.filter(
            branch=table.branch, is_available=True, product__status="ACTIVE"
        )
        .select_related("product", "product__category")
        .order_by("product__category__sort_order", "product__sort_order", "product__name")
    )
    lines, total = _cart_lines(request, table)
    return render(
        request,
        "menu/menu.html",
        {
            "table": table,
            "branch": table.branch,
            "products": products,
            "cart_lines": lines,
            "cart_total": total,
            "cart_count": sum(line["quantity"] for line in lines),
            "accepts_orders": table.can_accept_orders,
        },
    )


@require_http_methods(["POST"])
def cart_add(request, qr_token):
    table = _get_table(qr_token)
    cart = _load_cart(request, table.qr_token)
    branch_product_id = request.POST.get("branch_product_id")
    variant_id = request.POST.get("variant_id") or None
    quantity = max(1, int(request.POST.get("quantity", 1)))

    for entry in cart:
        if entry["branch_product_id"] == branch_product_id and entry.get("variant_id") == variant_id:
            entry["quantity"] += quantity
            break
    else:
        cart.append(
            {
                "branch_product_id": branch_product_id,
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
    _save_cart(request, table.qr_token, cart)
    _invalidate_checkout_key(request, table)
    return redirect("menu:menu", qr_token=table.qr_token)


@require_http_methods(["POST"])
def cart_remove(request, qr_token):
    table = _get_table(qr_token)
    cart = _load_cart(request, table.qr_token)
    index = int(request.POST.get("index", -1))
    if 0 <= index < len(cart):
        cart.pop(index)
    _save_cart(request, table.qr_token, cart)
    _invalidate_checkout_key(request, table)
    return redirect("menu:menu", qr_token=table.qr_token)


@require_http_methods(["GET", "POST"])
def checkout(request, qr_token):
    table = _get_table(qr_token)
    lines, total = _cart_lines(request, table)

    if not lines:
        messages.error(request, "Keranjang kosong.")
        return redirect("menu:menu", qr_token=table.qr_token)

    key = f"checkout_key_{table.qr_token}"
    order = None

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            customer = _resolve_customer(table, form)
            # Stable key while the cart is unchanged: a double submit resolves to
            # the same order instead of creating a duplicate (docs/PRD.md §6).
            idempotency_key = request.session.get(key) or str(uuid.uuid4())
            try:
                order, _created = services.checkout(
                    branch=table.branch,
                    table=table,
                    customer=customer,
                    customer_note=form.cleaned_data["customer_note"],
                    payment_method=form.cleaned_data["payment_method"],
                    source=OrderSource.QR,
                    items=[
                        {
                            "branch_product_id": line["branch_product"].id,
                            "variant_id": line["variant"].id if line["variant"] else None,
                            "quantity": line["quantity"],
                        }
                        for line in lines
                    ],
                    idempotency_key=idempotency_key,
                )
            except services.OrderError as exc:
                messages.error(request, str(exc))
            except IntegrityError:
                # Lost the idempotency race: the other request already created it.
                order = Order.objects.filter(idempotency_key=idempotency_key).first()
                if order is None:
                    messages.error(request, "Checkout gagal, silakan coba lagi.")

            if order is not None:
                _save_cart(request, table.qr_token, [])
                request.session.pop(key, None)
                return redirect(
                    "menu:order_status", qr_token=table.qr_token, order_id=order.id
                )
    else:
        form = CheckoutForm()
        request.session.setdefault(key, str(uuid.uuid4()))

    return render(
        request,
        "menu/checkout.html",
        {"table": table, "form": form, "cart_lines": lines, "cart_total": total},
    )


def _resolve_customer(table, form) -> Customer | None:
    """Return an existing/created customer when the guest left contact details."""
    name = form.cleaned_data.get("customer_name", "").strip()
    phone = form.cleaned_data.get("customer_phone", "").strip()
    if not name and not phone:
        return None
    customer = None
    if phone:
        customer = Customer.objects.filter(tenant=table.branch.tenant, phone=phone).first()
    if customer is None:
        customer = Customer.objects.create(
            tenant=table.branch.tenant, name=name, phone=phone
        )
    return customer


def order_status(request, qr_token, order_id):
    table = _get_table(qr_token)
    order = get_object_or_404(
        Order.objects.prefetch_related("items", "status_history"),
        pk=order_id,
        table=table,
    )
    return render(
        request,
        "menu/order_status.html",
        {"table": table, "order": order},
    )
