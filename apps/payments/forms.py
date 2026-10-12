"""Payment and refund forms."""

from django import forms

from apps.core.forms import StyledFormMixin


class RefundForm(StyledFormMixin, forms.Form):
    amount = forms.DecimalField(label="Nominal refund", min_value=0, decimal_places=2)
    reason = forms.CharField(label="Alasan", max_length=255)

    def __init__(self, *args, payment=None, **kwargs):
        super().__init__(*args, **kwargs)
        if payment is not None:
            self.fields["amount"].max_value = payment.refundable_amount
            self.fields["amount"].initial = payment.refundable_amount
