"""Menu management forms. All querysets are tenant-scoped."""

from django import forms
from django.forms import inlineformset_factory

from apps.catalog.models import (
    BranchProduct,
    Category,
    Product,
    ProductVariant,
)
from apps.core.forms import StyledFormMixin


class CategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "sort_order", "is_active"]


class ProductForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "description", "image_url", "status", "sort_order"]

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields["category"].queryset = Category.objects.filter(tenant=tenant)


ProductVariantFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    fields=["name", "price_delta", "is_active", "sort_order"],
    extra=1,
    can_delete=True,
)


class BranchProductForm(StyledFormMixin, forms.ModelForm):
    """Branch price and availability for one product at the active branch."""

    class Meta:
        model = BranchProduct
        fields = ["price", "is_available", "track_stock"]
