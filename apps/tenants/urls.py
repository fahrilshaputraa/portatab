from django.urls import path

from apps.tenants import views

app_name = "tenants"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("switch/", views.switch_workspace, name="switch_workspace"),
    path("settings/", views.business_settings, name="settings"),
    path("branches/new/", views.branch_form, name="branch_create"),
    path("branches/<uuid:pk>/edit/", views.branch_form, name="branch_edit"),
    path(
        "branches/<uuid:pk>/toggle-orders/",
        views.branch_toggle_orders,
        name="branch_toggle_orders",
    ),
]
