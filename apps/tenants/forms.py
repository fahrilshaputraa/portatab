"""Tenant and branch management forms."""

from django import forms

from apps.core.forms import StyledFormMixin
from apps.tenants.models import Branch, Tenant


class BusinessProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ["name", "email", "phone"]


class OperationalPolicyForm(StyledFormMixin, forms.Form):
    """Tenant-level operational policy (stored in TenantSettings)."""

    cash_orders_to_kitchen = forms.BooleanField(
        label="Order tunai boleh masuk dapur sebelum dibayar",
        required=False,
        help_text=(
            "Kalau dimatikan, order tunai baru muncul di Kitchen Display setelah kasir "
            "mengonfirmasi pembayaran. Order digital selalu menunggu pembayaran lunas."
        ),
    )
    low_stock_threshold = forms.IntegerField(
        label="Ambang stok rendah",
        min_value=0,
        help_text="Stok tersedia pada atau di bawah angka ini ditandai di halaman Stok.",
    )


class BranchForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Branch
        fields = ["name", "code", "address", "phone", "timezone", "status", "accepts_orders"]
