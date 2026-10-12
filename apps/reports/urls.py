from django.urls import path

from apps.reports import views

app_name = "reports"

urlpatterns = [
    path("", views.sales, name="sales"),
    path("export/", views.sales_csv, name="export_csv"),
]
