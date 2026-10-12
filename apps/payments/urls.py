from django.urls import path

from apps.payments import views

app_name = "payments"

urlpatterns = [
    path("", views.payment_list, name="list"),
    path("<uuid:pk>/confirm-cash/", views.confirm_cash, name="confirm_cash"),
    path("<uuid:pk>/pay-digital/", views.initiate_digital, name="initiate_digital"),
    path("<uuid:pk>/refund/", views.refund_create, name="refund_create"),
    path("refunds/<uuid:pk>/approve/", views.refund_approve, name="refund_approve"),
    path("refunds/<uuid:pk>/complete/", views.refund_complete, name="refund_complete"),
    path("refunds/<uuid:pk>/process/", views.refund_process, name="refund_process"),
]
