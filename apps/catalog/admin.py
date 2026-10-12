from django.contrib import admin

from apps.catalog.models import (
    BranchProduct,
    BranchProductVariant,
    Category,
    Product,
    ProductVariant,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "category", "status", "sort_order")
    list_filter = ("status",)
    search_fields = ("name",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "price_delta", "is_active")


class BranchProductVariantInline(admin.TabularInline):
    model = BranchProductVariant
    extra = 0


@admin.register(BranchProduct)
class BranchProductAdmin(admin.ModelAdmin):
    list_display = ("product", "branch", "price", "on_hand", "reserved", "track_stock")
    list_filter = ("track_stock", "is_available")
    search_fields = ("product__name",)
    inlines = [BranchProductVariantInline]
