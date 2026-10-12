"""Tenant isolation: one business can never read or change another's data."""

import pytest
from django.urls import reverse

from apps.catalog.models import Category, Product


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
