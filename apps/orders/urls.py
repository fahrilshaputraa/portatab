from django.urls import path

from apps.orders import views

app_name = "orders"

urlpatterns = [
    path("orders/", views.cashier, name="cashier"),
    path("orders/<uuid:pk>/", views.order_detail, name="detail"),
    path("orders/<uuid:pk>/accept/", views.accept_order, name="accept"),
    path("orders/<uuid:pk>/reject/", views.reject_order, name="reject"),
    path("orders/<uuid:pk>/complete/", views.complete_order, name="complete"),
    path("kitchen/", views.kitchen, name="kitchen"),
    path("kitchen/board/", views.kitchen_board, name="kitchen_board"),
    path("kitchen/<uuid:pk>/prepare/", views.start_preparing, name="prepare"),
    path("kitchen/<uuid:pk>/ready/", views.mark_ready, name="ready"),
]
