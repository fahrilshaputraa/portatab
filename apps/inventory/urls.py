from django.urls import path

from apps.inventory import views

app_name = "inventory"

urlpatterns = [
    path("", views.inventory_list, name="list"),
    path("<uuid:pk>/adjust/", views.stock_adjust, name="adjust"),
]
