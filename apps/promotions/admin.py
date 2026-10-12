from django.contrib import admin

from apps.promotions.models import Promotion, PromotionRedemption


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "discount_type", "status", "starts_at", "ends_at")
    list_filter = ("status", "discount_type")
    search_fields = ("code", "name")


@admin.register(PromotionRedemption)
class PromotionRedemptionAdmin(admin.ModelAdmin):
    list_display = ("promotion", "order", "customer", "discount_amount", "status")
    list_filter = ("status",)
