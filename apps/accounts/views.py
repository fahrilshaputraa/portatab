"""Sign-in, sign-out, owner registration and invitation acceptance."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.accounts import services
from apps.accounts.forms import (
    EmailAuthenticationForm,
    InvitationAcceptForm,
    RegistrationForm,
)
from apps.accounts.models import Invitation, MembershipStatus, User

BACKEND = "apps.accounts.backends.EmailOrUsernameBackend"


class PortatapLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user, tenant, branch = form.save()
            login(request, user, backend=BACKEND)
            request.session["active_tenant_id"] = str(tenant.id)
            request.session["active_branch_id"] = str(branch.id)
            messages.success(request, "Bisnis berhasil didaftarkan. Selamat datang!")
            return redirect("tenants:dashboard")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def invitation_accept(request, token):
    """Activate a staff invitation.

    A brand-new invitee sets a password here (possession of the emailed token
    proves control of the address). An invitee who already has an account must
    sign in first, so a leaked link cannot attach someone else's account.
    """
    invitation = get_object_or_404(
        Invitation.objects.select_related("tenant", "role"), token=token
    )
    expired = invitation.expires_at <= timezone.now()
    if invitation.status != MembershipStatus.INVITED or expired:
        return render(
            request,
            "accounts/invitation_accept.html",
            {"invitation": invitation, "unavailable": True},
        )

    existing = User.objects.filter(email=invitation.email.lower()).first()
    needs_password = existing is None

    if not needs_password and (
        not request.user.is_authenticated or request.user.pk != existing.pk
    ):
        messages.info(
            request, "Akun untuk email ini sudah ada. Masuk dulu untuk menerima undangan."
        )
        return redirect(f"{reverse('accounts:login')}?next={request.path}")

    form = InvitationAcceptForm(request.POST or None)

    if request.method == "POST":
        if needs_password and form.is_valid():
            user, _membership = services.accept_invitation(
                invitation=invitation,
                name=form.cleaned_data["name"],
                password=form.cleaned_data["password1"],
            )
        elif not needs_password:
            user, _membership = services.accept_invitation(invitation=invitation)
        else:
            user = None

        if user is not None:
            login(request, user, backend=BACKEND)
            request.session["active_tenant_id"] = str(invitation.tenant_id)
            request.session.pop("active_branch_id", None)
            messages.success(request, f"Anda bergabung ke {invitation.tenant.name}.")
            return redirect("tenants:dashboard")

    return render(
        request,
        "accounts/invitation_accept.html",
        {
            "invitation": invitation,
            "form": form,
            "needs_password": needs_password,
        },
    )
