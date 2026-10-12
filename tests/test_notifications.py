"""Notification inbox: creation through the order flow, reading and isolation."""

import pytest
from django.urls import reverse

from apps.notifications.models import Notification, NotificationEventType
from apps.orders import services as order_services
from apps.payments.models import PaymentMethod


def _order(branch, branch_product, table):
    order, _ = order_services.checkout(
        branch=branch,
        table=table,
        items=[{"branch_product_id": branch_product.id, "quantity": 1}],
        payment_method=PaymentMethod.CASH,
    )
    return order


@pytest.mark.django_db
def test_checkout_notifies_staff_who_can_accept(branch, branch_product, table, cashier):
    order = _order(branch, branch_product, table)

    notification = Notification.objects.get(
        user=cashier, event_type=NotificationEventType.ORDER_NEW, order=order
    )
    assert order.order_number in notification.title
    assert notification.read_at is None


@pytest.mark.django_db
def test_checkout_does_not_notify_users_without_the_permission(
    branch, branch_product, table, owner
):
    """The owner has every permission, so they are notified too — but a kitchen-only
    role must not receive an 'accept this order' notification."""
    from django.contrib.auth import get_user_model

    from apps.accounts.models import Role
    from apps.accounts.roles import RoleCode
    from apps.accounts.services import create_membership

    kitchen_user = get_user_model().objects.create_user(
        email="dapur@example.com", password="pass12345", name="Dapur"
    )
    create_membership(
        tenant=branch.tenant, user=kitchen_user, role_code=RoleCode.KITCHEN, branches=[branch]
    )
    _order(branch, branch_product, table)

    assert not Notification.objects.filter(
        user=kitchen_user, event_type=NotificationEventType.ORDER_NEW
    ).exists()
    assert Role.objects.filter(tenant=branch.tenant, code=RoleCode.KITCHEN).exists()


@pytest.mark.django_db
def test_inbox_renders_with_unread_badge(client, cashier, branch, branch_product, table):
    _order(branch, branch_product, table)
    client.force_login(cashier)

    response = client.get(reverse("notifications:list"))

    assert response.status_code == 200
    body = response.content.decode()
    assert "Notifikasi" in body
    assert "1 belum dibaca" in body


@pytest.mark.django_db
def test_mark_read(client, cashier):
    notification = Notification.objects.create(
        user=cashier,
        event_type=NotificationEventType.ORDER_NEW,
        title="Order baru",
    )
    client.force_login(cashier)

    response = client.post(reverse("notifications:mark_read", args=[notification.pk]))

    assert response.status_code == 302
    notification.refresh_from_db()
    assert notification.read_at is not None


@pytest.mark.django_db
def test_mark_all_read(client, cashier):
    for index in range(3):
        Notification.objects.create(
            user=cashier,
            event_type=NotificationEventType.ORDER_NEW,
            title=f"Order {index}",
        )
    client.force_login(cashier)

    client.post(reverse("notifications:mark_all_read"))

    assert Notification.objects.filter(user=cashier, read_at__isnull=True).count() == 0


@pytest.mark.django_db
def test_cannot_read_another_users_notification(client, cashier, owner):
    notification = Notification.objects.create(
        user=owner,
        event_type=NotificationEventType.ORDER_NEW,
        title="Punya owner",
    )
    client.force_login(cashier)

    response = client.post(reverse("notifications:mark_read", args=[notification.pk]))

    assert response.status_code == 404
    notification.refresh_from_db()
    assert notification.read_at is None
