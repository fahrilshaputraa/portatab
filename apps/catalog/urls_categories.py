from django.urls import path

from apps.catalog import views

app_name = "catalog_categories"

urlpatterns = [
    path("", views.category_list, name="list"),
    path("new/", views.category_form, name="create"),
    path("<uuid:pk>/edit/", views.category_form, name="edit"),
    path("<uuid:pk>/deactivate/", views.category_delete, name="deactivate"),
]
