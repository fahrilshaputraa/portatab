from django.contrib import admin

from apps.orders.models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "branch",
        "order_status",
        "payment_status",
        "total",
        "is_late",
        "created_at",
    )
    list_filter = ("order_status", "payment_status", "is_late")
    search_fields = ("order_number",)
    inlines = [OrderItemInline, OrderStatusHistoryInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("product_name_snapshot", "order", "quantity", "unit_price", "subtotal")
