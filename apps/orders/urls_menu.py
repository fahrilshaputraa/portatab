from django.urls import path

from apps.orders import menu_views

app_name = "menu"

urlpatterns = [
    path("<uuid:qr_token>/", menu_views.menu, name="menu"),
    path("<uuid:qr_token>/cart/add/", menu_views.cart_add, name="cart_add"),
    path("<uuid:qr_token>/cart/remove/", menu_views.cart_remove, name="cart_remove"),
    path("<uuid:qr_token>/checkout/", menu_views.checkout, name="checkout"),
    path(
        "<uuid:qr_token>/orders/<uuid:order_id>/",
        menu_views.order_status,
        name="order_status",
    ),
]
