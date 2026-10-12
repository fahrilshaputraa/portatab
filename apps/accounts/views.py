"""Sign-in, sign-out and owner registration views."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from apps.accounts.forms import EmailAuthenticationForm, RegistrationForm


class PortatapLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user, tenant, branch = form.save()
            login(request, user, backend="apps.accounts.backends.EmailOrUsernameBackend")
            request.session["active_tenant_id"] = str(tenant.id)
            request.session["active_branch_id"] = str(branch.id)
            messages.success(request, "Bisnis berhasil didaftarkan. Selamat datang!")
            return redirect("tenants:dashboard")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})
