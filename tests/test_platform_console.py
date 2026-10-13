"""Platform console: tenant administration, audit log and health view."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.orders import services as order_services
from apps.payments.models import PaymentMethod, PaymentProvider, PaymentWebhookEvent
from apps.platform_admin.models import PlatformAdminMembership
from apps.tenants.models import AuditLog, TenantStatus


@pytest.mark.django_db
def test_tenant_owner_cannot_open_the_console(client, owner):
    client.force_login(owner)

    for name in ["tenant_list", "audit_log", "health"]:
        assert client.get(reverse(f"platform_console:{name}")).status_code == 403


@pytest.mark.django_db
def test_anonymous_is_sent_to_login(client):
    response = client.get(reverse("platform_console:tenant_list"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


@pytest.mark.django_db
def test_platform_admin_can_list_tenants(client, platform_admin, tenant):
    client.force_login(platform_admin)

    response = client.get(reverse("platform_console:tenant_list"))

    assert response.status_code == 200
    body = response.content.decode()
    assert tenant.name in body
    assert "Starter" in body  # the tenant's trial plan is shown


@pytest.mark.django_db
def test_platform_admin_can_search_tenants(client, platform_admin, tenant, other_tenant):
    client.force_login(platform_admin)

    body = client.get(
        reverse("platform_console:tenant_list"), {"q": "bakso"}
    ).content.decode()

    assert "Bakso Lain" in body
    assert "Kopi Senja" not in body


@pytest.mark.django_db
def test_platform_admin_sees_tenant_detail(client, platform_admin, tenant, branch, owner):
    client.force_login(platform_admin)

    response = client.get(reverse("platform_console:tenant_detail", args=[tenant.pk]))

    assert response.status_code == 200
    body = response.content.decode()
    assert tenant.name in body
    assert branch.name in body


@pytest.mark.django_db
def test_suspending_a_tenant_is_audited_and_reversible(client, platform_admin, tenant):
    client.force_login(platform_admin)

    suspend = client.post(reverse("platform_console:tenant_status", args=[tenant.pk]))

    assert suspend.status_code == 302
    tenant.refresh_from_db()
    assert tenant.status == TenantStatus.SUSPENDED
    assert AuditLog.objects.filter(action="platform.tenant_status_changed").exists()

    client.post(reverse("platform_console:tenant_status", args=[tenant.pk]))
    tenant.refresh_from_db()
    assert tenant.status == TenantStatus.ACTIVE


@pytest.mark.django_db
def test_suspended_tenant_stops_accepting_orders(client, platform_admin, tenant, branch):
    client.force_login(platform_admin)
    client.post(reverse("platform_console:tenant_status", args=[tenant.pk]))

    branch.refresh_from_db()
    assert branch.can_accept_orders is False


@pytest.mark.django_db
def test_audit_log_lists_and_filters_actions(client, platform_admin, tenant):
    AuditLog.objects.create(tenant=tenant, action="refund.completed")
    AuditLog.objects.create(tenant=tenant, action="order.created")
    client.force_login(platform_admin)

    everything = client.get(reverse("platform_console:audit_log")).content.decode()
    filtered = client.get(
        reverse("platform_console:audit_log"), {"action": "refund"}
    ).content.decode()

    assert "refund.completed" in everything and "order.created" in everything
    assert "refund.completed" in filtered
    assert "order.created" not in filtered


@pytest.mark.django_db
def test_health_surfaces_problems(client, platform_admin, branch, branch_product, table):
    order, _ = order_services.checkout(
        branch=branch,
        table=table,
        items=[{"branch_product_id": branch_product.id, "quantity": 1}],
        payment_method=PaymentMethod.DIGITAL,
    )
    payment = order.payments.get()
    payment.created_at = timezone.now() - timedelta(hours=2)
    payment.status = "PENDING"
    payment.save(update_fields=["created_at", "status"])
    PaymentWebhookEvent.objects.create(
        provider=PaymentProvider.MIDTRANS,
        event_key="abc",
        payload={},
        signature_valid=False,
    )
    client.force_login(platform_admin)

    body = client.get(reverse("platform_console:health")).content.decode()

    assert "Pembayaran digital menggantung" in body
    assert "Webhook gagal / belum diproses" in body


@pytest.mark.django_db
def test_granting_platform_admin_makes_the_console_reachable(client, owner):
    from apps.platform_admin.services import grant_platform_admin

    tenant_owner = owner
    client.force_login(tenant_owner)
    assert client.get(reverse("platform_console:tenant_list")).status_code == 403

    grant_platform_admin(tenant_owner)

    assert client.get(reverse("platform_console:tenant_list")).status_code == 200
    assert PlatformAdminMembership.objects.filter(user=tenant_owner).exists()


@pytest.mark.django_db
def test_tenant_search_empty_state_and_reset(client, platform_admin, tenant):
    client.force_login(platform_admin)

    body = client.get(
        reverse("platform_console:tenant_list"), {"q": "missing-business"}
    ).content.decode()

    assert "Tenant tidak ditemukan" in body
    assert 'for="tenant-search"' in body
    assert 'value="missing-business"' in body
    assert '>Reset</a>' in body
    assert 'aria-current="page"' in body


@pytest.mark.django_db
def test_suspended_tenant_detail_shows_orders_paused(client, platform_admin, tenant, branch):
    tenant.status = TenantStatus.SUSPENDED
    tenant.save(update_fields=["status"])
    client.force_login(platform_admin)

    body = client.get(
        reverse("platform_console:tenant_detail", args=[tenant.pk])
    ).content.decode()

    assert "Dijeda" in body
    assert "Menerima order" not in body
    assert "Aktifkan tenant" in body
    assert 'scope="col"' in body
