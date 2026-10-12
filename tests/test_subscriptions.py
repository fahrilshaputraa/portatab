"""Subscriptions: trial, plan change, invoices, vouchers and plan limits."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Membership
from apps.accounts.roles import RoleCode
from apps.accounts.services import invite_staff
from apps.subscriptions import services
from apps.subscriptions.models import (
    Plan,
    PlanStatus,
    Subscription,
    SubscriptionInvoice,
    SubscriptionStatus,
    SubscriptionVoucher,
    SubscriptionVoucherRedemption,
    VoucherStatus,
)
from apps.tenants.models import Branch
from apps.tenants.services import register_business


def _voucher(**overrides) -> SubscriptionVoucher:
    defaults = {
        "code": "EARLYBIRD",
        "discount_type": "FIXED",
        "discount_value": Decimal("10000"),
        "duration_months": 3,
        "status": VoucherStatus.ACTIVE,
    }
    defaults.update(overrides)
    return SubscriptionVoucher.objects.create(**defaults)


# ------------------------------------------------------------------ trial ---


@pytest.mark.django_db
def test_onboarding_starts_a_trial(owner, branch, tenant):
    subscription = services.current_subscription(tenant)

    assert subscription is not None
    assert subscription.status == SubscriptionStatus.TRIALING
    assert subscription.trial_ends_at is not None
    assert subscription.plan.code == "STARTER"


@pytest.mark.django_db
def test_register_business_starts_a_trial():
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.create_user(
        email="baru@example.com", password="pass12345", name="Baru"
    )
    tenant, _branch = register_business(
        owner=user, business_name="Warung Baru", branch_name="Pusat"
    )

    assert services.current_subscription(tenant).status == SubscriptionStatus.TRIALING


@pytest.mark.django_db
def test_start_trial_is_idempotent(tenant):
    first = services.current_subscription(tenant)
    second = services.start_trial(tenant=tenant)

    assert first.pk == second.pk
    assert Subscription.objects.filter(tenant=tenant).count() == 1


# ----------------------------------------------------------------- limits ---


@pytest.mark.django_db
def test_entry_plan_limits_branches(tenant, branch):
    used, limit = services.usage(tenant)["branches"]
    assert (used, limit) == (1, 1)

    with pytest.raises(services.SubscriptionError):
        services.assert_can_add_branch(tenant)


@pytest.mark.django_db
def test_entry_plan_limits_accounts(tenant, owner):
    # The owner fixture already added one account; the plan allows five.
    for index in range(4):
        invite_staff(
            tenant=tenant, email=f"staf{index}@example.com", role_code=RoleCode.CASHIER
        )

    used, limit = services.usage(tenant)["accounts"]
    assert (used, limit) == (5, 5)

    with pytest.raises(services.SubscriptionError):
        invite_staff(tenant=tenant, email="kelebihan@example.com", role_code=RoleCode.CASHIER)


@pytest.mark.django_db
def test_subscribing_to_a_bigger_plan_raises_the_limits(tenant, branch, owner):
    services.subscribe(tenant=tenant, plan=Plan.objects.get(code="GROWTH"))

    assert services.within_branch_limit(tenant) is True
    assert services.plan_limits(tenant) == (3, 15)


# -------------------------------------------------------------- subscribing --


@pytest.mark.django_db
def test_subscribe_activates_plan_and_issues_invoice(tenant):
    plan = Plan.objects.get(code="GROWTH")

    subscription, invoice = services.subscribe(tenant=tenant, plan=plan)

    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.trial_ends_at is None
    assert subscription.plan == plan
    assert invoice.status == "ISSUED"
    assert invoice.normal_amount == plan.monthly_price
    assert invoice.total_amount == plan.monthly_price
    assert invoice.price_snapshot["plan_code"] == "GROWTH"


@pytest.mark.django_db
def test_invoice_keeps_its_price_snapshot_when_the_plan_price_changes(tenant):
    plan = Plan.objects.get(code="GROWTH")
    _subscription, invoice = services.subscribe(tenant=tenant, plan=plan)

    plan.monthly_price = Decimal("999000")
    plan.save(update_fields=["monthly_price"])

    invoice.refresh_from_db()
    assert invoice.normal_amount == Decimal("149000.00")
    assert invoice.price_snapshot["unit_price"] == "149000.00"


@pytest.mark.django_db
def test_invoice_numbers_are_unique(tenant):
    plan = Plan.objects.get(code="GROWTH")
    services.subscribe(tenant=tenant, plan=plan)
    services.subscribe(tenant=tenant, plan=plan)

    numbers = list(SubscriptionInvoice.objects.values_list("invoice_number", flat=True))
    assert len(numbers) == len(set(numbers)) == 2


# ---------------------------------------------------------------- vouchers --


@pytest.mark.django_db
def test_voucher_discounts_the_invoice_and_is_recorded(tenant):
    voucher = _voucher()

    _subscription, invoice = services.subscribe(
        tenant=tenant, plan=Plan.objects.get(code="STARTER"), voucher_code="earlybird"
    )

    assert invoice.discount_amount == Decimal("10000.00")
    assert invoice.total_amount == Decimal("39000.00")
    assert invoice.price_snapshot["voucher_code"] == "EARLYBIRD"

    voucher.refresh_from_db()
    assert voucher.redemption_count == 1
    assert SubscriptionVoucherRedemption.objects.filter(voucher=voucher, tenant=tenant).exists()


@pytest.mark.django_db
def test_voucher_can_only_be_used_once_per_tenant(tenant):
    _voucher()
    plan = Plan.objects.get(code="STARTER")
    services.subscribe(tenant=tenant, plan=plan, voucher_code="EARLYBIRD")

    with pytest.raises(services.SubscriptionError):
        services.subscribe(tenant=tenant, plan=plan, voucher_code="EARLYBIRD")


@pytest.mark.django_db
def test_voucher_quota_is_enforced(tenant):
    _voucher(quota=1)
    other = Branch.objects.create(tenant=tenant, name="X", code="X")

    services.subscribe(tenant=tenant, plan=Plan.objects.get(code="STARTER"), voucher_code="EARLYBIRD")

    with pytest.raises(services.SubscriptionError):
        services.assert_voucher_usable(voucher=SubscriptionVoucher.objects.get(), tenant=tenant)
    assert other.pk is not None


@pytest.mark.django_db
def test_expired_voucher_is_rejected(tenant):
    _voucher(valid_until=timezone.now() - timedelta(days=1))

    with pytest.raises(services.SubscriptionError):
        services.subscribe(
            tenant=tenant, plan=Plan.objects.get(code="STARTER"), voucher_code="EARLYBIRD"
        )


@pytest.mark.django_db
def test_unknown_voucher_code_is_ignored(tenant):
    _subscription, invoice = services.subscribe(
        tenant=tenant, plan=Plan.objects.get(code="STARTER"), voucher_code="TIDAKADA"
    )

    assert invoice.discount_amount == Decimal("0.00")


@pytest.mark.django_db
def test_inactive_plan_is_not_selectable_in_the_form():
    Plan.objects.filter(code="STARTER").update(status=PlanStatus.INACTIVE)
    from apps.subscriptions.forms import SubscribeForm

    codes = [plan.code for plan in SubscribeForm().fields["plan"].queryset]

    assert "STARTER" not in codes


# --------------------------------------------------------------------- UI ---


@pytest.mark.django_db
def test_owner_can_open_subscription_page(client, owner):
    client.force_login(owner)
    response = client.get(reverse("subscriptions:overview"))

    assert response.status_code == 200
    assert "Starter" in response.content.decode()


@pytest.mark.django_db
def test_owner_can_change_plan_through_the_page(client, owner, tenant):
    client.force_login(owner)

    response = client.post(
        reverse("subscriptions:overview"),
        {"plan": Plan.objects.get(code="BUSINESS").pk, "voucher_code": ""},
    )

    assert response.status_code == 302
    assert services.current_subscription(tenant).plan.code == "BUSINESS"


@pytest.mark.django_db
def test_manager_cannot_open_subscription_page(client, tenant, branch):
    from django.contrib.auth import get_user_model

    from apps.accounts.services import create_membership

    user = get_user_model().objects.create_user(
        email="mgr3@example.com", password="pass12345", name="Mgr"
    )
    create_membership(tenant=tenant, user=user, role_code=RoleCode.MANAGER, branches=[branch])

    client.force_login(user)
    assert client.get(reverse("subscriptions:overview")).status_code == 403
    assert Membership.objects.filter(tenant=tenant, user=user).exists()
