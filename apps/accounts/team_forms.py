"""Team invitation and access forms."""

from django import forms

from apps.accounts.models import BranchMembership, MembershipStatus, Role
from apps.core.forms import StyledFormMixin
from apps.tenants.models import Branch


def _scope(role_field, branch_field, tenant) -> None:
    """Restrict both querysets to the tenant — never trust posted ids."""
    role_field.queryset = Role.objects.filter(tenant=tenant).order_by("name")
    branch_field.queryset = Branch.objects.filter(tenant=tenant).order_by("name")


class InviteStaffForm(StyledFormMixin, forms.Form):
    email = forms.EmailField(label="Email staf")
    role = forms.ModelChoiceField(queryset=Role.objects.none(), label="Role", empty_label=None)
    branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.none(),
        required=False,
        label="Akses cabang",
        help_text="Kosongkan untuk role yang melihat semua cabang (Owner/Manager).",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            _scope(self.fields["role"], self.fields["branches"], tenant)

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class MemberAccessForm(StyledFormMixin, forms.Form):
    role = forms.ModelChoiceField(queryset=Role.objects.none(), label="Role", empty_label=None)
    branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.none(),
        required=False,
        label="Akses cabang",
        widget=forms.CheckboxSelectMultiple,
    )
    status = forms.ChoiceField(label="Status", choices=MembershipStatus.choices)

    def __init__(self, *args, membership=None, **kwargs):
        super().__init__(*args, **kwargs)
        if membership is not None:
            _scope(self.fields["role"], self.fields["branches"], membership.tenant)
            self.fields["branches"].initial = [
                link.branch_id for link in BranchMembership.objects.filter(membership=membership)
            ]
