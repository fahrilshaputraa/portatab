"""Root URL configuration.

Portals (docs/PRD.md §4.1):

- ``/auth/``   — sign in / register
- ``/app/``    — owner + staff portal (tenant-scoped)
- ``/r/``      — public customer QR menu
- ``/webhooks/`` — external provider callbacks
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("apps.accounts.urls")),
    path("app/products/", include("apps.catalog.urls_products")),
    path("app/categories/", include("apps.catalog.urls_categories")),
    path("app/team/", include("apps.accounts.urls_team")),
    path("app/notifications/", include("apps.notifications.urls")),
    path("app/tables/", include("apps.tables.urls")),
    path("app/inventory/", include("apps.inventory.urls")),
    path("app/promotions/", include("apps.promotions.urls")),
    path("app/payments/", include("apps.payments.urls")),
    path("app/reports/", include("apps.reports.urls")),
    path("app/subscription/", include("apps.subscriptions.urls")),
    path("app/appearance/", include("apps.themes.urls")),
    path("app/", include("apps.orders.urls")),
    path("app/", include("apps.tenants.urls")),
    path("webhooks/", include("apps.payments.urls_webhooks")),
    path("r/", include("apps.orders.urls_menu")),
    path("manage/", include("apps.website.urls_manage")),
    path("manage/console/", include("apps.platform_admin.urls")),
    path("", include("apps.website.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
