from django.urls import path

from apps.catalog import views

app_name = "catalog_products"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("new/", views.product_form, name="create"),
    path("<uuid:pk>/edit/", views.product_form, name="edit"),
    path("<uuid:pk>/branches/", views.branch_pricing, name="branch_pricing"),
    path("<uuid:pk>/deactivate/", views.product_delete, name="deactivate"),
]
