"""Table and QR management forms."""

from django import forms

from apps.core.forms import StyledFormMixin
from apps.tables.models import Table


class TableForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Table
        fields = ["table_number", "name", "status"]
