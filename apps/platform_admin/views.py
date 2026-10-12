"""Platform administration console.

Restricted to platform admins: platform access is separate from tenant ownership
(docs/BUSINESS-RULES.md §2), and an admin is never implicitly a tenant owner.
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.orders.models import KITCHEN_ACTIVE_STATUSES, Order, OrderStatus, PaymentStatus
from apps.payments.models import Payment, PaymentWebhookEvent, Refund, RefundStatus
from apps.platform_admin.permissions import require_platform_admin
from apps.subscriptions.models import Subscription, SubscriptionStatus
from apps.tenants.models import AuditLog, Branch, Tenant, TenantStatus
from apps.tenants.services import record_audit

OPEN_SUBSCRIPTION_STATUSES = [
    SubscriptionStatus.TRIALING,
    SubscriptionStatus.ACTIVE,
    SubscriptionStatus.PAST_DUE,
]


@login_required
@require_platform_admin
def console_home(request):
    return redirect("platform_console:tenant_list")


@login_required
@require_platform_admin
def tenant_list(request):
    query = request.GET.get("q", "").strip()
    tenants = Tenant.objects.annotate(
        branch_count=Count("branches", distinct=True),
        product_count=Count("products", distinct=True),
        order_count=Count("branches__orders", distinct=True),
    ).order_by("-created_at")
    if query:
        tenants = tenants.filter(Q(name__icontains=query) | Q(slug__icontains=query))

    subscriptions = {
        subscription.tenant_id: subscription
        for subscription in Subscription.objects.filter(
            status__in=OPEN_SUBSCRIPTION_STATUSES
        ).select_related("plan")
    }

    rows = [(tenant, subscriptions.get(tenant.id)) for tenant in tenants]
    return render(
        request, "platform_admin/tenant_list.html", {"rows": rows, "query": query}
    )


@login_required
@require_platform_admin
def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    now = timezone.now()
    last_week = now - timedelta(days=7)

    context = {
        "tenant": tenant,
        "subscription": Subscription.objects.filter(
            tenant=tenant, status__in=OPEN_SUBSCRIPTION_STATUSES
        )
        .select_related("plan")
        .first(),
        "branches": Branch.objects.filter(tenant=tenant).order_by("name"),
        "orders_total": Order.objects.filter(branch__tenant=tenant).count(),
        "orders_open": Order.objects.filter(branch__tenant=tenant)
        .exclude(
            order_status__in=[
                OrderStatus.COMPLETED,
                OrderStatus.REJECTED,
                OrderStatus.CANCELLED,
            ]
        )
        .count(),
        "orders_last_7d": Order.objects.filter(
            branch__tenant=tenant, created_at__gte=last_week
        ).count(),
        "gross_last_7d": Order.objects.filter(
            branch__tenant=tenant,
            created_at__gte=last_week,
            order_status=OrderStatus.COMPLETED,
        ).aggregate(total=Sum("total"))["total"]
        or 0,
        "recent_audit": AuditLog.objects.filter(tenant=tenant).select_related("user")[:20],
    }
    return render(request, "platform_admin/tenant_detail.html", context)


@login_required
@require_platform_admin
@require_POST
def tenant_status(request, pk):
    """Suspend or reactivate a tenant. A platform action, always audited."""
    tenant = get_object_or_404(Tenant, pk=pk)
    previous = tenant.status
    tenant.status = (
        TenantStatus.SUSPENDED
        if previous == TenantStatus.ACTIVE
        else TenantStatus.ACTIVE
    )
    tenant.save(update_fields=["status", "updated_at"])
    record_audit(
        action="platform.tenant_status_changed",
        tenant=tenant,
        user=request.user,
        entity=tenant,
        before={"status": previous},
        after={"status": tenant.status},
        request=request,
    )
    messages.success(request, f"{tenant.name} sekarang {tenant.get_status_display()}.")
    return redirect("platform_console:tenant_detail", pk=tenant.pk)


@login_required
@require_platform_admin
def audit_log(request):
    logs = AuditLog.objects.select_related("tenant", "user").order_by("-created_at")
    action = request.GET.get("action", "").strip()
    if action:
        logs = logs.filter(action__icontains=action)
    return render(
        request, "platform_admin/audit_log.html", {"logs": logs[:300], "action": action}
    )


@login_required
@require_platform_admin
def health(request):
    """Operational signals worth a human's attention."""
    now = timezone.now()
    stale_cutoff = now - timedelta(minutes=30)

    context = {
        "tenants_total": Tenant.objects.count(),
        "tenants_active": Tenant.objects.filter(status=TenantStatus.ACTIVE).count(),
        "branches_total": Branch.objects.count(),
        "orders_today": Order.objects.filter(created_at__date=now.date()).count(),
        "orders_pending": Order.objects.filter(order_status=OrderStatus.PENDING).count(),
        "orders_late": Order.objects.filter(
            order_status=OrderStatus.PENDING, is_late=True
        ).count(),
        "orders_in_kitchen": Order.objects.filter(
            order_status__in=list(KITCHEN_ACTIVE_STATUSES)
        ).count(),
        "payments_stuck": Payment.objects.filter(
            status=PaymentStatus.PENDING, created_at__lt=stale_cutoff
        ).count(),
        "refunds_needing_followup": Refund.objects.filter(
            status__in=[RefundStatus.FAILED, RefundStatus.REQUESTED]
        ).count(),
        "subscriptions_past_due": Subscription.objects.filter(
            status=SubscriptionStatus.PAST_DUE
        ).count(),
        "trials_ending_soon": Subscription.objects.filter(
            status=SubscriptionStatus.TRIALING,
            trial_ends_at__isnull=False,
            trial_ends_at__lte=now + timedelta(days=3),
        ).count(),
        "unpaid_completed": Order.objects.filter(order_status=OrderStatus.COMPLETED)
        .exclude(payment_status=PaymentStatus.PAID)
        .count(),
        "webhooks_unprocessed": PaymentWebhookEvent.objects.filter(
            Q(processed_at__isnull=True) | Q(signature_valid=False)
        ).count(),
        "webhooks_recent": PaymentWebhookEvent.objects.order_by("-created_at")[:10],
    }
    return render(request, "platform_admin/health.html", context)
