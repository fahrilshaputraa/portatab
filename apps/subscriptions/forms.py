"""Subscription forms."""

from django import forms

from apps.core.forms import StyledFormMixin
from apps.subscriptions.models import Plan, PlanStatus


class SubscribeForm(StyledFormMixin, forms.Form):
    plan = forms.ModelChoiceField(queryset=Plan.objects.none(), label="Paket", empty_label=None)
    voucher_code = forms.CharField(
        label="Kode voucher (opsional)",
        max_length=64,
        required=False,
        help_text="Voucher langganan PortaTap, bukan kode promo makanan.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].queryset = Plan.objects.filter(status=PlanStatus.ACTIVE).order_by(
            "monthly_price"
        )
