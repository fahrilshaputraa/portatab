from django.contrib import admin

from apps.customers.models import Customer, CustomerAddress


class CustomerAddressInline(admin.TabularInline):
    model = CustomerAddress
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "tenant", "status")
    list_filter = ("status",)
    search_fields = ("name", "phone", "email")
    inlines = [CustomerAddressInline]
