"""Blog/news authoring form."""

from django import forms

from apps.core.forms import StyledFormMixin
from apps.website.models import Post


class PostForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Post
        fields = ["kind", "title", "excerpt", "body", "cover_image_url", "is_featured"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 18}),
            "excerpt": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "body": "Markdown didukung: ## judul, - daftar, **tebal**, [tautan](https://…).",
        }
