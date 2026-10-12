"""End-to-end HTTP flow: register → menu → checkout → cashier → payment → kitchen."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Membership, MembershipStatus
from apps.accounts.roles import RoleCode
from apps.catalog.models import BranchProduct, Category, Product
from apps.orders import services as order_services
from apps.orders.models import Order, OrderStatus
from apps.payments.models import PaymentMethod, PaymentStatus
from apps.tenants.models import Branch, Tenant

User = get_user_model()


@pytest.mark.django_db
def test_owner_registration_creates_tenant_branch_and_membership(client):
    response = client.post(
        reverse("accounts:register"),
        {
            "name": "Sari",
            "email": "sari@example.com",
            "password1": "rahasia12345",
            "password2": "rahasia12345",
            "business_name": "Warung Sari",
            "branch_name": "Pusat",
        },
    )

    assert response.status_code == 302
    assert Tenant.objects.count() == 1
    tenant = Tenant.objects.get()
    assert Branch.objects.filter(tenant=tenant).count() == 1
    membership = Membership.objects.get(tenant=tenant)
    assert membership.role.code == RoleCode.OWNER
    assert membership.status == MembershipStatus.ACTIVE


@pytest.mark.django_db
def test_full_order_flow_over_http(client, owner, cashier, branch, branch_product, table):
    # 1. Customer opens the QR menu.
    menu_response = client.get(reverse("menu:menu", args=[table.qr_token]))
    assert menu_response.status_code == 200
    assert "Kopi Susu" in menu_response.content.decode()

    # 2. Adds to cart and checks out with cash.
    cart_response = client.post(
        reverse("menu:cart_add", args=[table.qr_token]),
        {"branch_product_id": str(branch_product.id), "quantity": 2},
    )
    assert cart_response.status_code == 302

    checkout = client.post(
        reverse("menu:checkout", args=[table.qr_token]), {"payment_method": PaymentMethod.CASH}
    )
    assert checkout.status_code == 302

    order = Order.objects.get()
    assert order.order_status == OrderStatus.PENDING
    assert order.total == Decimal("30000.00")

    # 3. Order status page renders.
    status_page = client.get(reverse("menu:order_status", args=[table.qr_token, order.id]))
    assert status_page.status_code == 200

    # 4. Cashier accepts the order (HTMX fragment response).
    client.force_login(cashier)
    accept = client.post(reverse("orders:accept", args=[order.id]))
    assert accept.status_code == 200
    order.refresh_from_db()
    assert order.order_status == OrderStatus.CONFIRMED

    # 5. Cash payment is confirmed.
    payment = order.payments.get()
    confirm = client.post(reverse("payments:confirm_cash", args=[payment.id]))
    assert confirm.status_code == 302
    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == PaymentStatus.PAID
    assert order.payment_status == PaymentStatus.PAID

    # 6. The paid order shows up in the kitchen queue.
    kitchen = client.get(reverse("orders:kitchen"))
    assert kitchen.status_code == 200
    assert order.order_number in kitchen.content.decode()


@pytest.mark.django_db
def test_cashier_cannot_act_on_another_tenants_order(
    client, owner, other_tenant, other_branch, table
):
    other_category = Category.objects.create(tenant=other_tenant, name="Lain")
    other_product = Product.objects.create(
        tenant=other_tenant, category=other_category, name="Produk Lain"
    )
    other_bp = BranchProduct.objects.create(
        branch=other_branch, product=other_product, price=Decimal("1000")
    )
    foreign_order, _ = order_services.checkout(
        branch=other_branch,
        items=[{"branch_product_id": other_bp.id, "quantity": 1}],
        payment_method=PaymentMethod.CASH,
    )

    client.force_login(owner)
    response = client.post(reverse("orders:accept", args=[foreign_order.id]))
    assert response.status_code == 404
