"""Customer promotions: eligibility, discount maths, quota safety and release."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.customers.models import Customer
from apps.orders import services as order_services
from apps.orders.models import Order
from apps.payments.models import PaymentMethod
from apps.promotions.models import (
    DiscountType,
    Promotion,
    PromotionRedemption,
    PromotionStatus,
    RedemptionStatus,
)

SUBTOTAL = Decimal("30000.00")


def _promo(tenant, **overrides) -> Promotion:
    defaults = {
        "code": "HEMAT",
        "name": "Hemat",
        "discount_type": DiscountType.FIXED,
        "discount_value": Decimal("10000"),
        "status": PromotionStatus.ACTIVE,
    }
    defaults.update(overrides)
    return Promotion.objects.create(tenant=tenant, **defaults)


def _checkout(branch, branch_product, table, *, code=None, customer=None, quantity=2):
    return order_services.checkout(
        branch=branch,
        table=table,
        items=[{"branch_product_id": branch_product.id, "quantity": quantity}],
        payment_method=PaymentMethod.CASH,
        promotion_code=code,
        customer=customer,
    )


# --------------------------------------------------------------- discount ---


@pytest.mark.django_db
def test_fixed_discount_is_applied(tenant, branch, branch_product, table):
    _promo(tenant)

    order, _ = _checkout(branch, branch_product, table, code="HEMAT")

    assert order.subtotal == SUBTOTAL
    assert order.discount_total == Decimal("10000.00")
    assert order.total == Decimal("20000.00")
    redemption = PromotionRedemption.objects.get(order=order)
    assert redemption.discount_amount == Decimal("10000.00")
    assert redemption.status == RedemptionStatus.APPLIED


@pytest.mark.django_db
def test_percentage_is_capped(tenant, branch, branch_product, table):
    _promo(
        tenant,
        discount_type=DiscountType.PERCENTAGE,
        discount_value=Decimal("50"),
        max_discount_amount=Decimal("4000"),
    )

    order, _ = _checkout(branch, branch_product, table, code="HEMAT")

    assert order.discount_total == Decimal("4000.00")
    assert order.total == Decimal("26000.00")


@pytest.mark.django_db
def test_discount_never_exceeds_subtotal(tenant, branch, branch_product, table):
    _promo(tenant, discount_value=Decimal("999999"))

    order, _ = _checkout(branch, branch_product, table, code="HEMAT")

    assert order.discount_total == SUBTOTAL
    assert order.total == Decimal("0.00")


@pytest.mark.django_db
def test_code_is_case_insensitive(tenant, branch, branch_product, table):
    _promo(tenant)

    order, _ = _checkout(branch, branch_product, table, code="hemat")

    assert order.discount_total == Decimal("10000.00")


# ------------------------------------------------------------ eligibility ---


@pytest.mark.django_db
def test_unknown_code_is_rejected(tenant, branch, branch_product, table):
    with pytest.raises(order_services.OrderError):
        _checkout(branch, branch_product, table, code="TIDAKADA")

    assert not Order.objects.exists()


@pytest.mark.django_db
def test_minimum_order_is_enforced(tenant, branch, branch_product, table):
    _promo(tenant, min_order_amount=Decimal("50000"))

    with pytest.raises(order_services.OrderError):
        _checkout(branch, branch_product, table, code="HEMAT")


@pytest.mark.django_db
def test_expired_code_is_rejected(tenant, branch, branch_product, table):
    _promo(tenant, ends_at=timezone.now() - timedelta(hours=1))

    with pytest.raises(order_services.OrderError):
        _checkout(branch, branch_product, table, code="HEMAT")


@pytest.mark.django_db
def test_inactive_code_is_rejected(tenant, branch, branch_product, table):
    _promo(tenant, status=PromotionStatus.INACTIVE)

    with pytest.raises(order_services.OrderError):
        _checkout(branch, branch_product, table, code="HEMAT")


@pytest.mark.django_db
def test_branch_restriction_is_enforced(tenant, branch, other_branch, branch_product, table):
    promotion = _promo(tenant)
    promotion.branches.set([other_branch])

    with pytest.raises(order_services.OrderError):
        _checkout(branch, branch_product, table, code="HEMAT")


@pytest.mark.django_db
def test_quota_is_enforced(tenant, branch, branch_product, table):
    _promo(tenant, total_quota=1)

    _checkout(branch, branch_product, table, code="HEMAT")

    with pytest.raises(order_services.OrderError):
        _checkout(branch, branch_product, table, code="HEMAT")


@pytest.mark.django_db
def test_per_customer_limit_is_enforced(tenant, branch, branch_product, table):
    _promo(tenant, per_customer_limit=1)
    customer = Customer.objects.create(tenant=tenant, name="Sari", phone="0811")

    _checkout(branch, branch_product, table, code="HEMAT", customer=customer)

    with pytest.raises(order_services.OrderError):
        _checkout(branch, branch_product, table, code="HEMAT", customer=customer)


@pytest.mark.django_db
def test_other_customer_still_gets_their_own_quota(tenant, branch, branch_product, table):
    _promo(tenant, per_customer_limit=1)
    first = Customer.objects.create(tenant=tenant, name="Sari", phone="0811")
    second = Customer.objects.create(tenant=tenant, name="Budi", phone="0812")

    _checkout(branch, branch_product, table, code="HEMAT", customer=first)
    order, _ = _checkout(branch, branch_product, table, code="HEMAT", customer=second)

    assert order.discount_total == Decimal("10000.00")


# ------------------------------------------------------------ releasing -----


@pytest.mark.django_db
def test_rejecting_an_order_returns_the_quota(tenant, branch, branch_product, table, cashier):
    _promo(tenant, total_quota=1)
    order, _ = _checkout(branch, branch_product, table, code="HEMAT")

    order_services.reject_order(order=order, actor=cashier, reason="Habis")

    assert PromotionRedemption.objects.get(order=order).status == RedemptionStatus.RELEASED
    # The freed slot can be used again.
    second, _ = _checkout(branch, branch_product, table, code="HEMAT")
    assert second.discount_total == Decimal("10000.00")


# ------------------------------------------------------------------- CRUD ---


@pytest.mark.django_db
def test_owner_can_create_promotion(client, owner, tenant):
    client.force_login(owner)

    response = client.post(
        reverse("promotions:create"),
        {
            "code": "newyear",
            "name": "Promo Tahun Baru",
            "discount_type": DiscountType.PERCENTAGE,
            "discount_value": "15",
            "min_order_amount": "20000",
            "total_quota": "100",
            "status": PromotionStatus.ACTIVE,
        },
    )

    assert response.status_code == 302
    promotion = Promotion.objects.get(tenant=tenant)
    assert promotion.code == "NEWYEAR"  # normalised to upper case
    assert promotion.discount_type == DiscountType.PERCENTAGE


@pytest.mark.django_db
def test_cashier_cannot_manage_promotions(client, cashier):
    client.force_login(cashier)

    assert client.get(reverse("promotions:list")).status_code == 200  # view-only
    assert client.get(reverse("promotions:create")).status_code == 403
