"""Stock services.

All stock changes go through here so reservation is atomic and every change is
ledgered (docs/BUSINESS-RULES.md §11). ``select_for_update`` on the branch product
serialises concurrent checkouts so the same stock can never be sold twice.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import BranchProduct
from apps.inventory.models import (
    MovementType,
    ReservationStatus,
    StockMovement,
    StockReservation,
)

if TYPE_CHECKING:
    from apps.accounts.models import User
    from apps.orders.models import Order


class InsufficientStock(Exception):
    """Raised when a reservation would sell more than the available quantity."""


def _record_movement(
    *,
    branch_product: BranchProduct,
    movement_type: str,
    quantity_delta: int,
    reason: str = "",
    order: Order | None = None,
    actor: User | None = None,
    reference_type: str = "",
    reference_id=None,
) -> StockMovement:
    return StockMovement.objects.create(
        branch_product=branch_product,
        movement_type=movement_type,
        quantity_delta=quantity_delta,
        stock_after=branch_product.on_hand,
        reserved_after=branch_product.reserved,
        reason=reason,
        order=order,
        created_by=actor,
        reference_type=reference_type,
        reference_id=reference_id,
    )


@transaction.atomic
def reserve_stock(
    *,
    order: Order,
    branch_product: BranchProduct,
    quantity: int,
    actor: User | None = None,
    ttl_minutes: int | None = None,
) -> StockReservation | None:
    """Atomically reserve ``quantity`` for ``order``. No-op for untracked products."""
    if quantity <= 0:
        raise ValueError("Kuantitas reservasi harus lebih dari 0.")

    product = BranchProduct.objects.select_for_update().get(pk=branch_product.pk)
    if not product.track_stock:
        return None

    reservation = (
        StockReservation.objects.select_for_update()
        .filter(order=order, branch_product=product)
        .first()
    )

    if product.available < quantity:
        raise InsufficientStock(
            f"Stok {product.product.name} tidak cukup: tersedia {product.available}, "
            f"diminta {quantity}."
        )

    product.reserved += quantity
    product.save(update_fields=["reserved", "updated_at"])

    if reservation is None:
        ttl = (
            settings.STOCK_RESERVATION_TTL_MINUTES if ttl_minutes is None else ttl_minutes
        )
        reservation = StockReservation.objects.create(
            order=order,
            branch_product=product,
            quantity=quantity,
            expires_at=timezone.now() + timedelta(minutes=ttl) if ttl else None,
        )
    else:
        reservation.quantity += quantity
        reservation.status = ReservationStatus.RESERVED
        reservation.save(update_fields=["quantity", "status"])

    _record_movement(
        branch_product=product,
        movement_type=MovementType.RESERVE,
        quantity_delta=quantity,
        reason="Reservasi checkout",
        order=order,
        actor=actor,
        reference_type="StockReservation",
        reference_id=reservation.id,
    )
    return reservation


@transaction.atomic
def release_reservation(
    *, reservation: StockReservation, actor: User | None = None, reason: str = ""
) -> StockReservation:
    """Return a still-reserved quantity to availability. Idempotent."""
    reservation = StockReservation.objects.select_for_update().get(pk=reservation.pk)
    if reservation.status != ReservationStatus.RESERVED:
        return reservation

    product = BranchProduct.objects.select_for_update().get(pk=reservation.branch_product_id)
    product.reserved = max(0, product.reserved - reservation.quantity)
    product.save(update_fields=["reserved", "updated_at"])

    reservation.status = ReservationStatus.RELEASED
    reservation.save(update_fields=["status"])

    _record_movement(
        branch_product=product,
        movement_type=MovementType.RELEASE,
        quantity_delta=-reservation.quantity,
        reason=reason or "Pelepasan reservasi",
        order=reservation.order,
        actor=actor,
        reference_type="StockReservation",
        reference_id=reservation.id,
    )
    return reservation


@transaction.atomic
def consume_reservation(
    *, reservation: StockReservation, actor: User | None = None, reason: str = ""
) -> StockReservation:
    """Turn a reservation into consumed stock when preparation starts. Idempotent."""
    reservation = StockReservation.objects.select_for_update().get(pk=reservation.pk)
    if reservation.status != ReservationStatus.RESERVED:
        return reservation

    product = BranchProduct.objects.select_for_update().get(pk=reservation.branch_product_id)
    product.reserved = max(0, product.reserved - reservation.quantity)
    product.on_hand = max(0, product.on_hand - reservation.quantity)
    product.save(update_fields=["reserved", "on_hand", "updated_at"])

    reservation.status = ReservationStatus.CONSUMED
    reservation.save(update_fields=["status"])

    _record_movement(
        branch_product=product,
        movement_type=MovementType.CONSUME,
        quantity_delta=-reservation.quantity,
        reason=reason or "Konsumsi saat mulai diproses",
        order=reservation.order,
        actor=actor,
        reference_type="StockReservation",
        reference_id=reservation.id,
    )
    return reservation


def release_order_reservations(
    *, order: Order, actor: User | None = None, reason: str = ""
) -> int:
    """Release every reservation still held by an order (rejection/cancellation)."""
    released = 0
    reservations = order.stock_reservations.filter(status=ReservationStatus.RESERVED)
    for reservation in reservations.select_related("branch_product"):
        release_reservation(reservation=reservation, actor=actor, reason=reason)
        released += 1
    return released


def consume_order_reservations(
    *, order: Order, actor: User | None = None, reason: str = ""
) -> int:
    """Consume every reservation held by an order (preparation started)."""
    consumed = 0
    reservations = order.stock_reservations.filter(status=ReservationStatus.RESERVED)
    for reservation in reservations.select_related("branch_product"):
        consume_reservation(reservation=reservation, actor=actor, reason=reason)
        consumed += 1
    return consumed


@transaction.atomic
def adjust_stock(
    *,
    branch_product: BranchProduct,
    quantity_delta: int,
    actor: User,
    reason: str,
    movement_type: str = MovementType.ADJUSTMENT,
) -> StockMovement:
    """Manual stock correction. Requires an actor and a reason for auditability."""
    if quantity_delta == 0:
        raise ValueError("Perubahan stok tidak boleh nol.")
    if not reason:
        raise ValueError("Alasan koreksi stok wajib diisi.")

    product = BranchProduct.objects.select_for_update().get(pk=branch_product.pk)
    new_on_hand = product.on_hand + quantity_delta
    if new_on_hand < 0:
        raise InsufficientStock("Stok tidak boleh menjadi negatif.")
    if new_on_hand < product.reserved:
        raise InsufficientStock("Stok fisik tidak boleh lebih kecil dari jumlah yang direservasi.")

    product.on_hand = new_on_hand
    product.save(update_fields=["on_hand", "updated_at"])

    return _record_movement(
        branch_product=product,
        movement_type=movement_type,
        quantity_delta=quantity_delta,
        reason=reason,
        actor=actor,
    )
