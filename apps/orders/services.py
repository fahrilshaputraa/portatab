"""Ordering services: checkout, status transitions and cashier timers.

The backend is the source of truth for prices, availability and transitions
(docs/BUSINESS-RULES.md §4, §6–7). Views call these functions; they never
compute totals or move status themselves.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.roles import Perm
from apps.catalog.models import BranchProduct, BranchProductVariant, ProductVariant
from apps.inventory.services import (
    consume_order_reservations,
    release_order_reservations,
    reserve_stock,
)
from apps.notifications.models import NotificationEventType
from apps.notifications.services import notify_order_event
from apps.orders.models import (
    Order,
    OrderItem,
    OrderSource,
    OrderStatus,
    OrderStatusHistory,
)
from apps.payments.services import create_payment_for_order
from apps.promotions import services as promotion_services
from apps.tenants.services import record_audit

if TYPE_CHECKING:
    from apps.accounts.models import User


class OrderError(Exception):
    """Base class for order-domain failures."""


class InvalidOrderTransition(OrderError):
    pass


class PaymentNotVerified(OrderError):
    pass


def compute_unit_price(*, branch_product: BranchProduct, variant: ProductVariant | None = None):
    """Authoritative unit price: branch price + variant delta, or branch override."""
    if variant is None:
        return branch_product.price
    override = BranchProductVariant.objects.filter(
        branch_product=branch_product, variant=variant
    ).first()
    if override is not None and override.price_override is not None:
        return override.price_override
    return branch_product.price + variant.price_delta


def generate_order_number(branch) -> str:
    today = timezone.localdate()
    count = Order.objects.filter(branch=branch, created_at__date=today).count()
    return f"{branch.code}-{today:%y%m%d}-{count + 1:04d}"


def _create_order_with_number(**fields) -> Order:
    """Create the order, retrying on the rare order-number race."""
    branch = fields["branch"]
    for attempt in range(5):
        try:
            with transaction.atomic():
                return Order.objects.create(
                    order_number=generate_order_number(branch),
                    pending_since=timezone.now(),
                    **fields,
                )
        except IntegrityError:
            if attempt == 4:
                raise
    raise OrderError("Gagal membuat nomor order.")  # pragma: no cover


@transaction.atomic
def checkout(
    *,
    branch,
    items: list[dict],
    payment_method: str,
    table=None,
    table_session=None,
    customer=None,
    customer_note: str = "",
    source: str = OrderSource.QR,
    actor: User | None = None,
    idempotency_key: str | None = None,
    promotion_code: str | None = None,
) -> tuple[Order, bool]:
    """Create one order from a validated cart. Returns ``(order, created)``.

    Prices and availability are recalculated here; a retried request with the same
    idempotency key returns the original order instead of a duplicate.
    """
    if idempotency_key:
        existing = Order.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            return existing, False

    if not branch.can_accept_orders:
        raise OrderError("Cabang sedang tidak menerima order baru.")
    if table is not None and not table.can_accept_orders:
        raise OrderError("Meja tidak dapat menerima order baru.")
    if not items:
        raise OrderError("Order harus memiliki minimal satu item.")

    lines = []
    subtotal = Decimal("0.00")
    for raw in items:
        branch_product = (
            BranchProduct.objects.select_for_update()
            .select_related("product")
            .get(pk=raw["branch_product_id"])
        )
        if branch_product.branch_id != branch.id:
            raise OrderError("Produk bukan milik cabang ini.")
        if not branch_product.is_sellable:
            raise OrderError(f"{branch_product.product.name} sedang tidak tersedia.")

        variant = None
        if raw.get("variant_id"):
            variant = ProductVariant.objects.filter(
                pk=raw["variant_id"], product=branch_product.product, is_active=True
            ).first()
            if variant is None:
                raise OrderError("Varian produk tidak valid.")

        quantity = int(raw["quantity"])
        if quantity <= 0:
            raise OrderError("Kuantitas harus lebih dari 0.")

        unit_price = compute_unit_price(branch_product=branch_product, variant=variant)
        line_subtotal = unit_price * quantity
        subtotal += line_subtotal
        lines.append(
            {
                "branch_product": branch_product,
                "variant": variant,
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": line_subtotal,
                "notes": raw.get("notes", ""),
                "options": raw.get("options"),
            }
        )

    # A promotion discount is recalculated here; the browser never supplies it.
    discount_total = Decimal("0.00")
    promotion = None
    if promotion_code:
        promotion = promotion_services.find_promotion(
            tenant=branch.tenant, code=promotion_code
        )
        if promotion is None:
            raise OrderError("Kode promo tidak ditemukan.")
        try:
            promotion, discount_total = promotion_services.lock_and_evaluate(
                promotion=promotion, subtotal=subtotal, branch=branch, customer=customer
            )
        except promotion_services.PromotionError as exc:
            raise OrderError(str(exc)) from exc

    order = _create_order_with_number(
        branch=branch,
        table=table,
        table_session=table_session,
        customer=customer,
        customer_note=customer_note,
        order_source=source,
        subtotal=subtotal,
        discount_total=discount_total,
        total=subtotal - discount_total,
        idempotency_key=idempotency_key,
    )

    for line in lines:
        OrderItem.objects.create(
            order=order,
            product=line["branch_product"].product,
            variant=line["variant"],
            product_name_snapshot=line["branch_product"].product.name,
            variant_name_snapshot=line["variant"].name if line["variant"] else "",
            unit_price=line["unit_price"],
            quantity=line["quantity"],
            subtotal=line["subtotal"],
            notes=line["notes"],
            options_snapshot=line["options"],
        )
        reserve_stock(
            order=order,
            branch_product=line["branch_product"],
            quantity=line["quantity"],
            actor=actor,
        )

    OrderStatusHistory.objects.create(
        order=order,
        changed_by=actor,
        from_status="",
        to_status=OrderStatus.PENDING,
        reason="Checkout",
    )
    if promotion is not None:
        promotion_services.record_redemption(
            promotion=promotion,
            order=order,
            customer=customer,
            discount=discount_total,
        )
    create_payment_for_order(order=order, method=payment_method)
    record_audit(
        action="order.created",
        tenant=branch.tenant,
        user=actor,
        entity=order,
        after={"total": str(order.total), "source": source},
    )
    notify_order_event(
        order=order,
        event_type=NotificationEventType.ORDER_NEW,
        permission_code=Perm.ORDERS_ACCEPT,
        title=f"Order baru {order.order_number}",
        message=f"Order baru di {order.branch.name} menunggu keputusan kasir.",
    )
    return order, True


@transaction.atomic
def transition_order(
    *, order: Order, to_status: str, actor: User | None = None, reason: str = ""
) -> Order:
    """Move an order through an allowed transition, with side effects."""
    order = Order.objects.select_for_update().get(pk=order.pk)

    if not order.can_transition_to(to_status):
        raise InvalidOrderTransition(
            f"Transisi {order.order_status} -> {to_status} tidak diizinkan."
        )
    if to_status == OrderStatus.PREPARING and not order.can_enter_kitchen:
        raise PaymentNotVerified(
            "Order digital belum dibayar; tidak boleh masuk antrean dapur."
        )

    from_status = order.order_status
    now = timezone.now()
    order.order_status = to_status
    update_fields = ["order_status", "updated_at"]

    if to_status == OrderStatus.CONFIRMED:
        order.confirmed_at = now
        order.reviewed_by = actor
        update_fields += ["confirmed_at", "reviewed_by"]
    elif to_status == OrderStatus.REJECTED:
        order.rejected_at = now
        order.rejection_reason = reason
        order.reviewed_by = actor
        update_fields += ["rejected_at", "rejection_reason", "reviewed_by"]
    elif to_status == OrderStatus.COMPLETED:
        order.completed_at = now
        update_fields += ["completed_at"]

    order.save(update_fields=update_fields)
    OrderStatusHistory.objects.create(
        order=order,
        changed_by=actor,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
    )

    if to_status in {OrderStatus.REJECTED, OrderStatus.CANCELLED}:
        release_order_reservations(
            order=order, actor=actor, reason=reason or "Order ditolak/dibatalkan"
        )
        promotion_services.release_promotions(order=order)
    elif to_status == OrderStatus.PREPARING:
        consume_order_reservations(order=order, actor=actor, reason="Mulai diproses")
    elif to_status == OrderStatus.READY:
        notify_order_event(
            order=order,
            event_type=NotificationEventType.ORDER_READY,
            permission_code=Perm.ORDERS_VIEW,
            title=f"Order {order.order_number} siap disajikan",
            message="Pesanan siap disajikan ke pelanggan.",
        )

    record_audit(
        action=f"order.{to_status.lower()}",
        tenant=order.branch.tenant,
        user=actor,
        entity=order,
        before={"order_status": from_status},
        after={"order_status": to_status},
    )
    return order


def accept_order(*, order: Order, actor) -> Order:
    return transition_order(order=order, to_status=OrderStatus.CONFIRMED, actor=actor)


def reject_order(*, order: Order, actor, reason: str) -> Order:
    return transition_order(
        order=order, to_status=OrderStatus.REJECTED, actor=actor, reason=reason
    )


def start_preparing(*, order: Order, actor) -> Order:
    return transition_order(order=order, to_status=OrderStatus.PREPARING, actor=actor)


def mark_ready(*, order: Order, actor) -> Order:
    return transition_order(order=order, to_status=OrderStatus.READY, actor=actor)


def complete_order(*, order: Order, actor) -> Order:
    return transition_order(order=order, to_status=OrderStatus.COMPLETED, actor=actor)


def cancel_order(*, order: Order, actor, reason: str) -> Order:
    return transition_order(
        order=order, to_status=OrderStatus.CANCELLED, actor=actor, reason=reason
    )


def evaluate_pending_orders(*, branch=None, now=None) -> dict[str, int]:
    """Apply the 3-minute warning and 5-minute late flags to pending orders.

    Idempotent: ``warned_at`` and ``is_late`` guard repeated notifications.
    """
    now = now or timezone.now()
    query = Order.objects.filter(order_status=OrderStatus.PENDING)
    if branch is not None:
        query = query.filter(branch=branch)

    warned = 0
    late = 0
    for order in query:
        age = (now - order.pending_since).total_seconds()
        if age >= settings.ORDER_LATE_SECONDS and not order.is_late:
            order.is_late = True
            order.late_since = now
            order.save(update_fields=["is_late", "late_since", "updated_at"])
            notify_order_event(
                order=order,
                event_type=NotificationEventType.ORDER_LATE,
                permission_code=Perm.ORDERS_ACCEPT,
                title=f"Order {order.order_number} terlambat",
                message="Order sudah lebih dari 5 menit tanpa keputusan kasir.",
            )
            late += 1
        if age >= settings.ORDER_WARNING_SECONDS and order.warned_at is None:
            order.warned_at = now
            order.save(update_fields=["warned_at", "updated_at"])
            notify_order_event(
                order=order,
                event_type=NotificationEventType.ORDER_WARNING,
                permission_code=Perm.ORDERS_ACCEPT,
                title=f"Order {order.order_number} belum direspons",
                message="Order sudah lebih dari 3 menit tanpa keputusan kasir.",
            )
            warned += 1
    return {"warned": warned, "late": late}
