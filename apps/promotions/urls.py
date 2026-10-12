from django.urls import path

from apps.promotions import views

app_name = "promotions"

urlpatterns = [
    path("", views.promotion_list, name="list"),
    path("new/", views.promotion_form, name="create"),
    path("<uuid:pk>/edit/", views.promotion_form, name="edit"),
]
