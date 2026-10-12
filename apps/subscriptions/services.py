"""Subscription services.

A subscription belongs to the tenant, never to a staff account, and its status is
separate from the tenant's operational status (docs/BUSINESS-RULES.md §13).
Invoices keep a price snapshot so a later plan-price change never rewrites
history, and plan limits are enforced here rather than in the UI.
"""

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import Invitation, Membership, MembershipStatus
from apps.subscriptions.models import (
    InvoiceStatus,
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

MONEY = Decimal("0.01")
OPEN_SUBSCRIPTION_STATUSES = [
    SubscriptionStatus.TRIALING,
    SubscriptionStatus.ACTIVE,
    SubscriptionStatus.PAST_DUE,
]
# Fallback limits used when a tenant has no usable plan (expired/cancelled).
FALLBACK_BRANCHES = 1
FALLBACK_ACCOUNTS = 5


class SubscriptionError(Exception):
    """Raised when a subscription action or a plan limit is violated."""


# --------------------------------------------------------------- reading ----


def current_subscription(tenant) -> Subscription | None:
    return (
        Subscription.objects.filter(tenant=tenant, status__in=OPEN_SUBSCRIPTION_STATUSES)
        .select_related("plan")
        .first()
    )


def active_plan(tenant) -> Plan | None:
    subscription = current_subscription(tenant)
    return subscription.plan if subscription is not None else None


def plan_limits(tenant) -> tuple[int, int]:
    plan = active_plan(tenant)
    if plan is None:
        return FALLBACK_BRANCHES, FALLBACK_ACCOUNTS
    return plan.max_branches, plan.max_accounts


def usage(tenant) -> dict[str, tuple[int, int]]:
    """Current usage against the plan limits, for display and enforcement.

    Account usage counts active members plus outstanding invitations, because an
    invitation has already reserved a seat.
    """
    branch_limit, account_limit = plan_limits(tenant)
    members = Membership.objects.filter(
        tenant=tenant,
        status__in=[MembershipStatus.ACTIVE, MembershipStatus.INVITED],
    ).count()
    pending_invites = Invitation.objects.filter(
        tenant=tenant, status=MembershipStatus.INVITED
    ).count()
    return {
        "branches": (Branch.objects.filter(tenant=tenant).count(), branch_limit),
        "accounts": (members + pending_invites, account_limit),
    }


def within_branch_limit(tenant) -> bool:
    used, limit = usage(tenant)["branches"]
    return used < limit


def within_account_limit(tenant) -> bool:
    used, limit = usage(tenant)["accounts"]
    return used < limit


def assert_can_add_branch(tenant) -> None:
    used, limit = usage(tenant)["branches"]
    if used >= limit:
        raise SubscriptionError(
            f"Paket Anda dibatasi {limit} cabang. Ubah paket untuk menambah cabang."
        )


def assert_can_add_account(tenant) -> None:
    used, limit = usage(tenant)["accounts"]
    if used >= limit:
        raise SubscriptionError(
            f"Paket Anda dibatasi {limit} akun. Ubah paket untuk menambah anggota."
        )


# ---------------------------------------------------------------- trial -----


@transaction.atomic
def start_trial(*, tenant) -> Subscription | None:
    """Give a brand-new tenant the entry plan and a trial window."""
    if current_subscription(tenant) is not None:
        return current_subscription(tenant)

    plan = Plan.objects.filter(status=PlanStatus.ACTIVE).order_by("monthly_price").first()
    if plan is None:
        return None

    now = timezone.now()
    trial_end = now + timedelta(days=settings.SUBSCRIPTION_TRIAL_DAYS)
    return Subscription.objects.create(
        tenant=tenant,
        plan=plan,
        status=SubscriptionStatus.TRIALING,
        current_period_start=now.date(),
        current_period_end=trial_end.date(),
        trial_ends_at=trial_end,
    )


# ----------------------------------------------------------------- money ----


def voucher_or_none(code: str | None) -> SubscriptionVoucher | None:
    code = (code or "").strip()
    if not code:
        return None
    return SubscriptionVoucher.objects.filter(code__iexact=code).first()


def assert_voucher_usable(*, voucher, tenant) -> None:
    now = timezone.now()
    if voucher.status != VoucherStatus.ACTIVE:
        raise SubscriptionError("Voucher ini sedang tidak aktif.")
    if voucher.valid_from and now < voucher.valid_from:
        raise SubscriptionError("Voucher ini belum berlaku.")
    if voucher.valid_until and now > voucher.valid_until:
        raise SubscriptionError("Voucher ini sudah kedaluwarsa.")
    if voucher.quota is not None and voucher.redemption_count >= voucher.quota:
        raise SubscriptionError("Kuota voucher ini sudah habis.")
    if SubscriptionVoucherRedemption.objects.filter(voucher=voucher, tenant=tenant).exists():
        raise SubscriptionError("Voucher ini sudah pernah dipakai tenant Anda.")


def price_with_voucher(*, plan, voucher=None) -> tuple[Decimal, Decimal, Decimal]:
    """``(normal, discount, total)`` for one billing period."""
    normal = plan.monthly_price
    discount = Decimal("0.00")
    if voucher is not None:
        if voucher.discount_type == "PERCENTAGE":
            discount = normal * voucher.discount_value / Decimal("100")
        else:
            discount = voucher.discount_value
        discount = min(discount, normal)
        discount = discount.quantize(MONEY, rounding=ROUND_HALF_UP)
    return normal, discount, (normal - discount).quantize(MONEY, rounding=ROUND_HALF_UP)


def _next_invoice_number() -> str:
    today = timezone.localdate()
    count = SubscriptionInvoice.objects.filter(created_at__date=today).count()
    return f"INV-{today:%y%m%d}-{count + 1:04d}"


def generate_invoice(*, subscription, voucher=None) -> SubscriptionInvoice:
    """Issue an invoice carrying the price/period snapshot used at billing time."""
    normal, discount, total = price_with_voucher(plan=subscription.plan, voucher=voucher)
    now = timezone.now()
    snapshot = {
        "plan_code": subscription.plan.code,
        "plan_name": subscription.plan.name,
        "unit_price": str(normal),
        "voucher_code": voucher.code if voucher else None,
        "duration_months": voucher.duration_months if voucher else None,
        "period_start": subscription.current_period_start.isoformat()
        if subscription.current_period_start
        else None,
        "period_end": subscription.current_period_end.isoformat()
        if subscription.current_period_end
        else None,
    }

    for attempt in range(5):
        try:
            with transaction.atomic():
                return SubscriptionInvoice.objects.create(
                    subscription=subscription,
                    invoice_number=_next_invoice_number(),
                    normal_amount=normal,
                    discount_amount=discount,
                    total_amount=total,
                    currency=settings.CURRENCY_CODE,
                    status=InvoiceStatus.ISSUED,
                    price_snapshot=snapshot,
                    issued_at=now,
                    due_at=now + timedelta(days=7),
                )
        except IntegrityError:
            if attempt == 4:
                raise
    raise SubscriptionError("Gagal membuat nomor invoice.")  # pragma: no cover


@transaction.atomic
def redeem_voucher(*, voucher, tenant, subscription) -> SubscriptionVoucherRedemption:
    """Record a voucher redemption, locking the row so the quota cannot over-sell."""
    locked = SubscriptionVoucher.objects.select_for_update().get(pk=voucher.pk)
    assert_voucher_usable(voucher=locked, tenant=tenant)

    redemption = SubscriptionVoucherRedemption.objects.create(
        voucher=locked, tenant=tenant, subscription=subscription
    )
    locked.redemption_count += 1
    locked.save(update_fields=["redemption_count"])
    return redemption


@transaction.atomic
def subscribe(*, tenant, plan, voucher_code: str | None = None, actor=None):
    """Activate or change the tenant's plan and issue the first invoice."""
    voucher = voucher_or_none(voucher_code)
    if voucher is not None:
        assert_voucher_usable(voucher=voucher, tenant=tenant)

    subscription = current_subscription(tenant)
    today = timezone.localdate()
    if subscription is None:
        subscription = Subscription(tenant=tenant)

    subscription.plan = plan
    subscription.status = SubscriptionStatus.ACTIVE
    subscription.current_period_start = today
    subscription.current_period_end = today + timedelta(days=30)
    subscription.trial_ends_at = None
    subscription.save()

    if voucher is not None:
        redeem_voucher(voucher=voucher, tenant=tenant, subscription=subscription)

    invoice = generate_invoice(subscription=subscription, voucher=voucher)
    return subscription, invoice
