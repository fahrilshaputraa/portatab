from django.urls import path

from apps.platform_admin import views

app_name = "platform_console"

urlpatterns = [
    path("", views.console_home, name="home"),
    path("tenants/", views.tenant_list, name="tenant_list"),
    path("tenants/<uuid:pk>/", views.tenant_detail, name="tenant_detail"),
    path("tenants/<uuid:pk>/status/", views.tenant_status, name="tenant_status"),
    path("audit/", views.audit_log, name="audit_log"),
    path("health/", views.health, name="health"),
]
