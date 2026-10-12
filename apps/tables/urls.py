from django.urls import path

from apps.tables import views

app_name = "tables"

urlpatterns = [
    path("", views.table_list, name="list"),
    path("new/", views.table_form, name="create"),
    path("<uuid:pk>/edit/", views.table_form, name="edit"),
    path("<uuid:pk>/qr/", views.table_qr, name="qr"),
    path("<uuid:pk>/qr/rotate/", views.table_rotate_qr, name="rotate_qr"),
]
