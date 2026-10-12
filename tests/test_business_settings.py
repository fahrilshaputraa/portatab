"""Business settings: profile, branches and the operational kitchen policy."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.roles import RoleCode
from apps.accounts.services import create_membership
from apps.orders import services as order_services
from apps.orders.models import OrderStatus
from apps.orders.selectors import kitchen_queue
from apps.payments.models import PaymentMethod
from apps.tenants.models import Branch
from apps.tenants.services import (
    SETTING_CASH_ORDERS_TO_KITCHEN,
    cash_orders_to_kitchen,
    get_setting,
    low_stock_threshold,
    set_setting,
)


def _order(branch, branch_product, table, *, method=PaymentMethod.CASH):
    order, _ = order_services.checkout(
        branch=branch,
        table=table,
        items=[{"branch_product_id": branch_product.id, "quantity": 1}],
        payment_method=method,
    )
    return order


# ------------------------------------------------------------- settings -----


@pytest.mark.django_db
def test_owner_can_open_business_settings(client, owner):
    client.force_login(owner)
    assert client.get(reverse("tenants:settings")).status_code == 200


@pytest.mark.django_db
def test_manager_without_permission_cannot_open_settings(client, tenant, branch):
    user = get_user_model().objects.create_user(
        email="mgr@example.com", password="pass12345", name="Manager"
    )
    create_membership(tenant=tenant, user=user, role_code=RoleCode.MANAGER, branches=[branch])

    client.force_login(user)
    assert client.get(reverse("tenants:settings")).status_code == 403


@pytest.mark.django_db
def test_profile_update_is_saved(client, owner, tenant):
    client.force_login(owner)

    response = client.post(
        reverse("tenants:settings"),
        {
            "section": "profile",
            "name": "Kopi Senja Baru",
            "email": "halo@senja.test",
            "phone": "08123",
        },
    )

    assert response.status_code == 302
    tenant.refresh_from_db()
    assert tenant.name == "Kopi Senja Baru"
    assert tenant.email == "halo@senja.test"


@pytest.mark.django_db
def test_policy_update_is_saved(client, owner, tenant):
    client.force_login(owner)

    response = client.post(
        reverse("tenants:settings"), {"section": "policy", "low_stock_threshold": "12"}
    )

    assert response.status_code == 302
    # An unchecked checkbox is simply absent from the POST body.
    assert get_setting(tenant, SETTING_CASH_ORDERS_TO_KITCHEN) is False
    assert low_stock_threshold(tenant) == 12


@pytest.mark.django_db
def test_settings_fall_back_to_defaults(tenant):
    assert cash_orders_to_kitchen(tenant) is True
    assert low_stock_threshold(tenant) == 5


@pytest.mark.django_db
def test_setting_round_trip(tenant):
    set_setting(tenant, SETTING_CASH_ORDERS_TO_KITCHEN, False)
    assert cash_orders_to_kitchen(tenant) is False
    set_setting(tenant, SETTING_CASH_ORDERS_TO_KITCHEN, True)
    assert cash_orders_to_kitchen(tenant) is True


# -------------------------------------------------------------- branches ----


@pytest.mark.django_db
def test_owner_can_create_branch(client, owner, tenant):
    client.force_login(owner)

    response = client.post(
        reverse("tenants:branch_create"),
        {
            "name": "Cabang Dua",
            "code": "B2",
            "status": "ACTIVE",
            "accepts_orders": "on",
            "timezone": "Asia/Jakarta",
        },
    )

    assert response.status_code == 302
    assert Branch.objects.filter(tenant=tenant, code="B2").exists()


@pytest.mark.django_db
def test_owner_can_pause_order_acceptance(client, owner, branch):
    client.force_login(owner)

    response = client.post(reverse("tenants:branch_toggle_orders", args=[branch.pk]))

    assert response.status_code == 302
    branch.refresh_from_db()
    assert branch.accepts_orders is False
    assert branch.can_accept_orders is False


# -------------------------------------------- kitchen policy enforcement ----


@pytest.mark.django_db
def test_cash_order_enters_kitchen_when_policy_permits(branch, branch_product, table, cashier):
    order = _order(branch, branch_product, table)
    order_services.accept_order(order=order, actor=cashier)

    order_services.start_preparing(order=order, actor=cashier)
    order.refresh_from_db()
    assert order.order_status == OrderStatus.PREPARING


@pytest.mark.django_db
def test_cash_order_waits_when_policy_is_off(
    branch, branch_product, table, cashier, tenant
):
    set_setting(tenant, SETTING_CASH_ORDERS_TO_KITCHEN, False)
    order = _order(branch, branch_product, table)
    order_services.accept_order(order=order, actor=cashier)

    with pytest.raises(order_services.PaymentNotVerified):
        order_services.start_preparing(order=order, actor=cashier)


@pytest.mark.django_db
def test_kitchen_queue_respects_policy(branch, branch_product, table, cashier):
    order = _order(branch, branch_product, table)
    order_services.accept_order(order=order, actor=cashier)

    assert kitchen_queue(branch=branch, allow_cash_before_payment=True).count() == 1
    assert kitchen_queue(branch=branch, allow_cash_before_payment=False).count() == 0


@pytest.mark.django_db
def test_digital_order_never_enters_kitchen_before_payment(branch, branch_product, table, cashier):
    order = _order(branch, branch_product, table, method=PaymentMethod.DIGITAL)
    order_services.accept_order(order=order, actor=cashier)

    assert kitchen_queue(branch=branch, allow_cash_before_payment=True).count() == 0
    with pytest.raises(order_services.PaymentNotVerified):
        order_services.start_preparing(order=order, actor=cashier)
