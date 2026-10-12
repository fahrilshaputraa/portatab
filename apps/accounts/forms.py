"""Account forms: sign-in and owner registration."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction

from apps.core.forms import StyledFormMixin
from apps.tenants.services import register_business

User = get_user_model()


class EmailAuthenticationForm(StyledFormMixin, AuthenticationForm):
    """Sign-in form keyed by email."""

    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )


class RegistrationForm(StyledFormMixin, forms.Form):
    """Owner self-registration plus first tenant and branch."""

    name = forms.CharField(label="Nama Anda", max_length=255)
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(label="Kata sandi", widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(label="Ulangi kata sandi", widget=forms.PasswordInput)
    business_name = forms.CharField(label="Nama bisnis", max_length=255)
    branch_name = forms.CharField(label="Nama cabang pertama", max_length=255, initial="Cabang Utama")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email sudah terdaftar.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") and cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Kata sandi tidak sama.")
        return cleaned

    @transaction.atomic
    def save(self):
        """Create the user and onboard their first tenant/branch atomically."""
        data = self.cleaned_data
        user = User.objects.create_user(
            email=data["email"], password=data["password1"], name=data["name"]
        )
        tenant, branch = register_business(
            owner=user,
            business_name=data["business_name"],
            branch_name=data["branch_name"],
        )
        return user, tenant, branch
