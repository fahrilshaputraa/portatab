"""Smoke test: every portal page renders for an authorized owner."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    [
        "tenants:dashboard",
        "tenants:settings",
        "tenants:branch_create",
        "team:list",
        "team:invite",
        "notifications:list",
        "subscriptions:overview",
        "themes:editor",
        "themes:preview",
        "promotions:list",
        "promotions:create",
        "catalog_products:list",
        "catalog_products:create",
        "catalog_categories:list",
        "catalog_categories:create",
        "tables:list",
        "tables:create",
        "inventory:list",
        "orders:cashier",
        "orders:kitchen",
        "payments:list",
        "reports:sales",
        "reports:export_csv",
    ],
)
def test_portal_pages_render(client, owner, branch, table, branch_product, url_name):
    client.force_login(owner)
    response = client.get(reverse(url_name))
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    [
        "platform_console:tenant_list",
        "platform_console:audit_log",
        "platform_console:health",
    ],
)
def test_platform_console_pages_render(client, platform_admin, tenant, url_name):
    client.force_login(platform_admin)
    assert client.get(reverse(url_name)).status_code == 200


@pytest.mark.django_db
def test_table_qr_page_renders(client, owner, table):
    client.force_login(owner)
    response = client.get(reverse("tables:qr", args=[table.pk]))
    assert response.status_code == 200
    assert "<svg" in response.content.decode()


@pytest.mark.django_db
def test_branch_pricing_page_renders(client, owner, product):
    client.force_login(owner)
    response = client.get(reverse("catalog_products:branch_pricing", args=[product.pk]))
    assert response.status_code == 200


@pytest.mark.django_db
def test_auth_pages_render(client):
    assert client.get(reverse("accounts:login")).status_code == 200
    assert client.get(reverse("accounts:register")).status_code == 200
