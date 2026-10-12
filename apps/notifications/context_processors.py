"""Template context for the notification badge."""

from apps.notifications.models import Notification


def unread_notifications(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"unread_notifications": 0}
    return {
        "unread_notifications": Notification.objects.filter(
            user=user, read_at__isnull=True
        ).count()
    }
