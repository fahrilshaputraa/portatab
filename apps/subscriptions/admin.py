from django.contrib import admin

from apps.subscriptions.models import (
    Plan,
    Subscription,
    SubscriptionEvent,
    SubscriptionInvoice,
    SubscriptionPayment,
    SubscriptionVoucher,
    SubscriptionVoucherRedemption,
)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "monthly_price", "max_branches", "max_accounts", "status")
    list_filter = ("status",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("tenant", "plan", "status", "current_period_end", "trial_ends_at")
    list_filter = ("status",)


class SubscriptionPaymentInline(admin.TabularInline):
    model = SubscriptionPayment
    extra = 0


@admin.register(SubscriptionInvoice)
class SubscriptionInvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "subscription", "status", "total_amount", "issued_at")
    list_filter = ("status",)
    inlines = [SubscriptionPaymentInline]


@admin.register(SubscriptionVoucher)
class SubscriptionVoucherAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "quota", "status")
    list_filter = ("status",)


@admin.register(SubscriptionVoucherRedemption)
class SubscriptionVoucherRedemptionAdmin(admin.ModelAdmin):
    list_display = ("voucher", "tenant", "status", "redeemed_at")


@admin.register(SubscriptionEvent)
class SubscriptionEventAdmin(admin.ModelAdmin):
    list_display = ("subscription", "event_type", "created_at")
