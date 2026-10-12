from django.contrib import admin

from apps.inventory.models import StockMovement, StockReservation


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ("branch_product", "order", "quantity", "status", "expires_at")
    list_filter = ("status",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "branch_product",
        "movement_type",
        "quantity_delta",
        "stock_after",
        "reserved_after",
        "created_at",
    )
    list_filter = ("movement_type",)
    readonly_fields = [f.name for f in StockMovement._meta.fields]
