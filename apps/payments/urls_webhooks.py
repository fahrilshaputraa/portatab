from django.urls import path

from apps.payments import views

app_name = "payment_webhooks"

urlpatterns = [
    path("midtrans/", views.midtrans_webhook, name="midtrans"),
]
