"""Inventory forms."""

from django import forms

from apps.core.forms import StyledFormMixin


class StockAdjustForm(StyledFormMixin, forms.Form):
    """Manual stock correction; always recorded with an actor and a reason."""

    quantity_delta = forms.IntegerField(
        label="Perubahan stok", help_text="Positif menambah, negatif mengurangi."
    )
    reason = forms.CharField(label="Alasan", max_length=255)
