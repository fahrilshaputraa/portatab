"""Customer promotion services.

Eligibility and the final discount are always computed here, never trusted from
the browser (docs/BUSINESS-RULES.md §12). Quota checks run under a row lock on
the promotion so two concurrent checkouts cannot both take the last slot.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from apps.promotions.models import (
    DiscountType,
    Promotion,
    PromotionRedemption,
    PromotionStatus,
    RedemptionStatus,
)

MONEY = Decimal("0.01")


class PromotionError(Exception):
    """Raised when a promotion may not be used for this order."""


def find_promotion(*, tenant, code: str) -> Promotion | None:
    code = (code or "").strip()
    if not code:
        return None
    return Promotion.objects.filter(tenant=tenant, code__iexact=code).first()


def _redeemed(promotion) -> int:
    return PromotionRedemption.objects.filter(
        promotion=promotion, status=RedemptionStatus.APPLIED
    ).count()


def evaluate_promotion(*, promotion, subtotal, branch=None, customer=None) -> Decimal:
    """The discount this cart earns, or ``PromotionError`` explaining why not."""
    now = timezone.now()

    if promotion.status != PromotionStatus.ACTIVE:
        raise PromotionError("Kode promo ini sedang tidak aktif.")
    if promotion.starts_at and now < promotion.starts_at:
        raise PromotionError("Kode promo ini belum berlaku.")
    if promotion.ends_at and now > promotion.ends_at:
        raise PromotionError("Kode promo ini sudah kedaluwarsa.")

    if branch is not None:
        allowed = list(promotion.branches.all())
        if allowed and all(item.pk != branch.pk for item in allowed):
            raise PromotionError("Kode promo ini tidak berlaku di cabang ini.")

    if subtotal < promotion.min_order_amount:
        raise PromotionError(
            f"Minimal belanja Rp {promotion.min_order_amount} untuk memakai kode ini."
        )

    if promotion.total_quota is not None and _redeemed(promotion) >= promotion.total_quota:
        raise PromotionError("Kuota kode promo ini sudah habis.")

    if promotion.per_customer_limit is not None and customer is not None:
        used_by_customer = PromotionRedemption.objects.filter(
            promotion=promotion,
            customer=customer,
            status=RedemptionStatus.APPLIED,
        ).count()
        if used_by_customer >= promotion.per_customer_limit:
            raise PromotionError("Batas pemakaian kode ini untuk Anda sudah tercapai.")

    if promotion.discount_type == DiscountType.PERCENTAGE:
        discount = subtotal * promotion.discount_value / Decimal("100")
    else:
        discount = promotion.discount_value

    if promotion.max_discount_amount is not None:
        discount = min(discount, promotion.max_discount_amount)
    discount = min(discount, subtotal)  # a total can never go below zero
    return discount.quantize(MONEY, rounding=ROUND_HALF_UP)


def lock_and_evaluate(*, promotion, subtotal, branch=None, customer=None):
    """Lock the promotion row, then evaluate the discount.

    Call inside the checkout transaction so the quota check and the redemption
    that follows cannot interleave with another order.
    """
    locked = Promotion.objects.select_for_update().get(pk=promotion.pk)
    return locked, evaluate_promotion(
        promotion=locked, subtotal=subtotal, branch=branch, customer=customer
    )


def record_redemption(*, promotion, order, customer, discount) -> PromotionRedemption:
    return PromotionRedemption.objects.create(
        promotion=promotion,
        order=order,
        customer=customer,
        discount_amount=discount,
    )


@transaction.atomic
def release_promotions(*, order) -> int:
    """Return an order's redeemed promotions to the pool (rejection/cancellation)."""
    return PromotionRedemption.objects.filter(
        order=order, status=RedemptionStatus.APPLIED
    ).update(status=RedemptionStatus.RELEASED)
