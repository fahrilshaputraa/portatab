"""Menu appearance forms."""

from django import forms

from apps.core.forms import StyledFormMixin
from apps.themes.models import ThemeTemplate


class ThemeConfigForm(StyledFormMixin, forms.Form):
    template = forms.ModelChoiceField(
        queryset=ThemeTemplate.objects.none(), label="Template", empty_label=None
    )
    logo_url = forms.URLField(label="URL logo", required=False)
    banner_url = forms.URLField(label="URL banner", required=False)
    primary_color = forms.CharField(
        label="Warna utama",
        max_length=7,
        help_text="Kode HEX, misalnya #0068f9. Dipakai untuk harga dan tombol.",
    )
    layout = forms.ChoiceField(
        label="Tata letak menu",
        choices=[("list", "Daftar"), ("grid", "Grid")],
    )

    def __init__(self, *args, allowed_templates=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_templates is not None:
            self.fields["template"].queryset = ThemeTemplate.objects.filter(
                pk__in=[template.pk for template in allowed_templates]
            )
