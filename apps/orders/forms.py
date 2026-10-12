"""Order forms: rejection reason and customer checkout."""

from django import forms

from apps.core.forms import StyledFormMixin
from apps.payments.models import PaymentMethod


class RejectOrderForm(StyledFormMixin, forms.Form):
    reason = forms.CharField(label="Alasan penolakan", max_length=255)


class CheckoutForm(StyledFormMixin, forms.Form):
    """Customer checkout. The backend recalculates every price regardless."""

    payment_method = forms.ChoiceField(
        label="Metode pembayaran",
        choices=[
            (PaymentMethod.CASH, "Tunai (bayar di kasir)"),
            (PaymentMethod.DIGITAL, "Digital (Midtrans)"),
        ],
    )
    customer_name = forms.CharField(label="Nama (opsional)", max_length=255, required=False)
    customer_phone = forms.CharField(label="No. HP (opsional)", max_length=32, required=False)
    customer_note = forms.CharField(
        label="Catatan untuk dapur (opsional)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    promotion_code = forms.CharField(
        label="Kode promo (opsional)",
        max_length=64,
        required=False,
        help_text="Diskon dihitung ulang di server setelah kode diperiksa.",
    )
