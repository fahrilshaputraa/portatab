"""Tenant isolation: one business can never read or change another's data."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.catalog.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
def test_product_list_shows_only_own_tenant(client, owner, product, other_tenant):
    other_category = Category.objects.create(tenant=other_tenant, name="Rahasia")
    Product.objects.create(tenant=other_tenant, category=other_category, name="Produk Rahasia")

    client.force_login(owner)
    response = client.get(reverse("catalog_products:list"))

    body = response.content.decode()
    assert response.status_code == 200
    assert "Kopi Susu" in body
    assert "Produk Rahasia" not in body


@pytest.mark.django_db
def test_cross_tenant_product_edit_is_404(client, owner, other_tenant):
    other_category = Category.objects.create(tenant=other_tenant, name="Rahasia")
    foreign = Product.objects.create(
        tenant=other_tenant, category=other_category, name="Produk Rahasia"
    )

    client.force_login(owner)
    response = client.get(reverse("catalog_products:edit", args=[foreign.pk]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_unauthenticated_portal_redirects_to_login(client):
    response = client.get(reverse("tenants:dashboard"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


@pytest.mark.django_db
def test_platform_admin_login_goes_to_the_console(client, platform_admin):
    """A platform admin owns no business, so the dashboard is not their home."""
    response = client.post(
        reverse("accounts:login"),
        {"username": platform_admin.email, "password": "pass12345"},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("platform_console:home")


@pytest.mark.django_db
def test_owner_login_goes_to_the_dashboard(client, owner):
    response = client.post(
        reverse("accounts:login"),
        {"username": owner.email, "password": "pass12345"},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("tenants:dashboard")


@pytest.mark.django_db
def test_platform_admin_without_tenant_is_sent_to_the_console(client, platform_admin):
    """The tenant guard routes the admin to their own surface, not a bare 403."""
    client.force_login(platform_admin)

    response = client.get(reverse("tenants:dashboard"))

    assert response.status_code == 302
    assert response["Location"] == reverse("platform_console:home")


@pytest.mark.django_db
def test_account_without_membership_is_still_denied(client, tenant):
    """Tenant isolation must keep refusing an ordinary account with no membership."""
    user = User.objects.create_user(
        email="tanpa@example.com", password="pass12345", name="Tanpa Bisnis"
    )
    client.force_login(user)

    assert client.get(reverse("tenants:dashboard")).status_code == 403
