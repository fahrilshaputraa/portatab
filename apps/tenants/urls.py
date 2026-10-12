from django.urls import path

from apps.tenants import views

app_name = "tenants"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("switch/", views.switch_workspace, name="switch_workspace"),
]
