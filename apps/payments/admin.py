from django.contrib import admin

from apps.payments.models import (
    Payment,
    PaymentAttempt,
    PaymentWebhookEvent,
    Refund,
)


class PaymentAttemptInline(admin.TabularInline):
    model = PaymentAttempt
    extra = 0


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "method", "provider", "status", "amount", "paid_at")
    list_filter = ("method", "provider", "status")
    search_fields = ("order__order_number", "provider_reference")
    inlines = [PaymentAttemptInline]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("refund_number", "payment", "status", "amount", "completed_at")
    list_filter = ("status",)
    search_fields = ("refund_number",)


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_type", "signature_valid", "processed_at", "created_at")
    list_filter = ("provider", "signature_valid")
    readonly_fields = [f.name for f in PaymentWebhookEvent._meta.fields]
