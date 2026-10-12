"""Staff notification inbox."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.notifications.models import Notification
from apps.tenants.permissions import require_tenant


@login_required
@require_tenant
def notification_list(request):
    """Everything addressed to the signed-in user, newest first."""
    notifications = (
        Notification.objects.filter(user=request.user)
        .select_related("order", "branch")
        .order_by("-created_at")[:200]
    )
    return render(
        request,
        "notifications/list.html",
        {
            "notifications": notifications,
            "unread_count": Notification.objects.filter(
                user=request.user, read_at__isnull=True
            ).count(),
        },
    )


@login_required
@require_tenant
@require_POST
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return redirect(request.POST.get("next") or "notifications:list")


@login_required
@require_tenant
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, read_at__isnull=True).update(
        read_at=timezone.now()
    )
    return redirect("notifications:list")
