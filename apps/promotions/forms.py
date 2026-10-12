"""Promotion management forms."""

from django import forms

from apps.core.forms import StyledFormMixin
from apps.promotions.models import Promotion
from apps.tenants.models import Branch


class PromotionForm(StyledFormMixin, forms.ModelForm):
    """Owner-facing promotion editor. Branch choices are tenant-scoped by the view."""

    starts_at = forms.DateTimeField(
        label="Mulai berlaku",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
        ),
    )
    ends_at = forms.DateTimeField(
        label="Berakhir",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}
        ),
    )

    class Meta:
        model = Promotion
        fields = [
            "code",
            "name",
            "discount_type",
            "discount_value",
            "min_order_amount",
            "max_discount_amount",
            "total_quota",
            "per_customer_limit",
            "starts_at",
            "ends_at",
            "status",
            "branches",
        ]
        widgets = {"branches": forms.CheckboxSelectMultiple}

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields["branches"].queryset = Branch.objects.filter(tenant=tenant).order_by(
                "name"
            )

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()
