"""Payment reconciliation and provider refunds."""

from decimal import Decimal

import pytest
from django.core.management import call_command
from django.urls import reverse

from apps.orders import services as order_services
from apps.orders.models import PaymentStatus
from apps.payments import services as payment_services
from apps.payments.models import PaymentMethod, Refund, RefundStatus
from apps.payments.providers.midtrans import MidtransError


class StubClient:
    """Stands in for the provider so no test ever touches the network."""

    def __init__(self, *, status=None, refund=None, error=None):
        self._status = status or {}
        self._refund = refund or {}
        self._error = error

    @classmethod
    def from_settings(cls):
        raise AssertionError("the stub must be injected, not built from settings")

    def get_transaction_status(self, order_id):
        if self._error:
            raise self._error
        return self._status

    def refund(self, *, order_id, amount, reason=""):
        if self._error:
            raise self._error
        return self._refund


def _digital_order(branch, branch_product, table, quantity=1):
    order, _ = order_services.checkout(
        branch=branch,
        table=table,
        items=[{"branch_product_id": branch_product.id, "quantity": quantity}],
        payment_method=PaymentMethod.DIGITAL,
    )
    payment = order.payments.get()
    payment.provider_reference = f"PT-{payment.id}"
    payment.status = PaymentStatus.PENDING
    payment.save(update_fields=["provider_reference", "status"])
    return order, payment


def _inject(monkeypatch, client):
    """Force the provider client used by the command and the refund service."""
    factory = type("Stub", (), {"from_settings": classmethod(lambda cls: client)})
    monkeypatch.setattr(
        "apps.payments.management.commands.reconcile_payments.MidtransClient", factory
    )
    monkeypatch.setattr(
        "apps.payments.providers.midtrans.MidtransClient.from_settings",
        classmethod(lambda cls: client),
    )


# ------------------------------------------------------------ reconciling ---


@pytest.mark.django_db
def test_reconcile_marks_a_settled_payment_as_paid(
    monkeypatch, branch, branch_product, table
):
    order, payment = _digital_order(branch, branch_product, table)
    _inject(
        monkeypatch,
        StubClient(
            status={
                "transaction_status": "settlement",
                "transaction_id": "tx-1",
                "order_id": payment.provider_reference,
            }
        ),
    )

    call_command("reconcile_payments", "--minutes", "0")

    payment.refresh_from_db()
    order.refresh_from_db()
    assert payment.status == PaymentStatus.PAID
    assert order.payment_status == PaymentStatus.PAID


@pytest.mark.django_db
def test_reconcile_marks_an_expired_payment(monkeypatch, branch, branch_product, table):
    _order, payment = _digital_order(branch, branch_product, table)
    _inject(monkeypatch, StubClient(status={"transaction_status": "expire"}))

    call_command("reconcile_payments", "--minutes", "0")

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.EXPIRED


@pytest.mark.django_db
def test_dry_run_changes_nothing(monkeypatch, branch, branch_product, table):
    _order, payment = _digital_order(branch, branch_product, table)
    _inject(monkeypatch, StubClient(status={"transaction_status": "settlement"}))

    call_command("reconcile_payments", "--minutes", "0", "--dry-run")

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING


@pytest.mark.django_db
def test_provider_error_leaves_the_payment_untouched(
    monkeypatch, branch, branch_product, table
):
    _order, payment = _digital_order(branch, branch_product, table)
    _inject(monkeypatch, StubClient(error=MidtransError("jaringan bermasalah")))

    call_command("reconcile_payments", "--minutes", "0")

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING


@pytest.mark.django_db
def test_reconcile_never_downgrades_a_paid_payment(
    monkeypatch, branch, branch_product, table
):
    _order, payment = _digital_order(branch, branch_product, table)
    payment_services.apply_provider_status(payment=payment, new_status=PaymentStatus.PAID)
    payment.refresh_from_db()
    payment.status = PaymentStatus.PAID
    payment.provider_reference = f"PT-{payment.id}"
    payment.save(update_fields=["status", "provider_reference"])

    _inject(monkeypatch, StubClient(status={"transaction_status": "expire"}))
    call_command("reconcile_payments", "--minutes", "0")

    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PAID


# --------------------------------------------------------------- refunds ----


@pytest.mark.django_db
def test_digital_refund_records_provider_reference(branch, branch_product, table, owner):
    order, payment = _digital_order(branch, branch_product, table)
    payment_services.apply_provider_status(payment=payment, new_status=PaymentStatus.PAID)
    refund = payment_services.request_refund(
        payment=payment, actor=owner, amount=Decimal("15000"), reason="salah pesan"
    )

    result = payment_services.process_digital_refund(
        refund=refund, actor=owner, client=StubClient(refund={"refund_key": "rf-1"})
    )

    assert result.status == RefundStatus.SUCCEEDED
    assert result.provider_reference == "rf-1"
    # The original payment stays PAID after a refund.
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.PAID
    assert order.pk == result.payment.order_id


@pytest.mark.django_db
def test_failing_digital_refund_stays_visible(branch, branch_product, table, owner):
    _order, payment = _digital_order(branch, branch_product, table)
    payment_services.apply_provider_status(payment=payment, new_status=PaymentStatus.PAID)
    refund = payment_services.request_refund(
        payment=payment, actor=owner, amount=Decimal("15000"), reason="salah pesan"
    )

    result = payment_services.process_digital_refund(
        refund=refund, actor=owner, client=StubClient(error=MidtransError("ditolak"))
    )

    assert result.status == RefundStatus.FAILED
    assert "ditolak" in result.failure_reason


@pytest.mark.django_db
def test_cash_refund_cannot_go_through_the_provider(
    branch, branch_product, table, owner, cashier
):
    order, _ = order_services.checkout(
        branch=branch,
        table=table,
        items=[{"branch_product_id": branch_product.id, "quantity": 1}],
        payment_method=PaymentMethod.CASH,
    )
    payment = order.payments.get()
    payment_services.confirm_cash_payment(payment=payment, actor=cashier)
    refund = payment_services.request_refund(
        payment=payment, actor=cashier, amount=Decimal("15000"), reason="salah pesan"
    )

    with pytest.raises(payment_services.PaymentError):
        payment_services.process_digital_refund(
            refund=refund, actor=owner, client=StubClient()
        )


@pytest.mark.django_db
def test_process_view_requires_approval_permission(
    monkeypatch, client, owner, cashier, branch, branch_product, table
):
    _order, payment = _digital_order(branch, branch_product, table)
    payment_services.apply_provider_status(payment=payment, new_status=PaymentStatus.PAID)
    refund = payment_services.request_refund(
        payment=payment, actor=cashier, amount=Decimal("15000"), reason="salah pesan"
    )
    payment_services.approve_refund(refund=refund, actor=owner)
    _inject(monkeypatch, StubClient(refund={"refund_key": "rf-9"}))

    client.force_login(cashier)
    denied = client.post(reverse("payments:refund_process", args=[refund.pk]))
    assert denied.status_code == 403

    client.force_login(owner)
    allowed = client.post(reverse("payments:refund_process", args=[refund.pk]))
    assert allowed.status_code == 302
    refund.refresh_from_db()
    assert refund.status == RefundStatus.SUCCEEDED


@pytest.mark.django_db
def test_refund_view_rejects_another_tenants_refund(
    client, owner, other_tenant, other_branch, other_owner
):
    from apps.catalog.models import BranchProduct, Category, Product

    category = Category.objects.create(tenant=other_tenant, name="Lain")
    product = Product.objects.create(tenant=other_tenant, category=category, name="Produk Lain")
    branch_product = BranchProduct.objects.create(
        branch=other_branch, product=product, price=Decimal("1000")
    )
    order, _ = order_services.checkout(
        branch=other_branch,
        items=[{"branch_product_id": branch_product.id, "quantity": 1}],
        payment_method=PaymentMethod.DIGITAL,
    )
    payment = order.payments.get()
    payment_services.apply_provider_status(payment=payment, new_status=PaymentStatus.PAID)
    refund = payment_services.request_refund(
        payment=payment, actor=other_owner, amount=Decimal("1000"), reason="x"
    )
    assert Refund.objects.filter(pk=refund.pk).exists()

    client.force_login(owner)
    response = client.post(reverse("payments:refund_process", args=[refund.pk]))

    assert response.status_code == 404
