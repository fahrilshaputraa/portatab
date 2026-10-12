"""Team & access management (invite staff, set role and branch access)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts import services
from apps.accounts.models import Invitation, Membership, MembershipStatus
from apps.accounts.roles import Perm, RoleCode
from apps.accounts.selectors import (
    active_owner_count,
    pending_invitations,
    tenant_memberships,
)
from apps.accounts.team_forms import InviteStaffForm, MemberAccessForm
from apps.tenants.permissions import require_permission, require_tenant
from apps.tenants.services import record_audit


@login_required
@require_tenant
@require_permission(Perm.TEAM_MANAGE)
def team_list(request):
    return render(
        request,
        "accounts/team/list.html",
        {
            "members": tenant_memberships(request.tenant),
            "invitations": pending_invitations(request.tenant),
        },
    )


@login_required
@require_tenant
@require_permission(Perm.TEAM_MANAGE)
def invite_staff(request):
    if request.method == "POST":
        form = InviteStaffForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            membership, invitation = services.invite_staff(
                tenant=request.tenant,
                email=form.cleaned_data["email"],
                role_code=form.cleaned_data["role"].code,
                branches=list(form.cleaned_data["branches"]),
                actor=request.user,
            )
            if membership is not None:
                record_audit(
                    action="membership.created",
                    tenant=request.tenant,
                    user=request.user,
                    entity=membership,
                    request=request,
                )
                messages.success(request, f"{membership.user.email} langsung ditambahkan ke tim.")
            else:
                services.send_invitation_email(invitation=invitation, request=request)
                record_audit(
                    action="invitation.created",
                    tenant=request.tenant,
                    user=request.user,
                    entity=invitation,
                    request=request,
                )
                messages.success(request, f"Undangan dikirim ke {invitation.email}.")
            return redirect("team:list")
    else:
        form = InviteStaffForm(tenant=request.tenant)
    return render(request, "accounts/team/invite.html", {"form": form})


@login_required
@require_tenant
@require_permission(Perm.TEAM_MANAGE)
def member_edit(request, pk):
    membership = get_object_or_404(Membership, pk=pk, tenant=request.tenant)

    if request.method == "POST":
        form = MemberAccessForm(request.POST, membership=membership)
        if form.is_valid():
            new_role = form.cleaned_data["role"]
            new_status = form.cleaned_data["status"]

            # Never let the last owner lock the tenant out of its own admin.
            loses_owner = membership.role.code == RoleCode.OWNER and (
                new_role.code != RoleCode.OWNER or new_status != MembershipStatus.ACTIVE
            )
            if loses_owner and active_owner_count(request.tenant) <= 1:
                messages.error(request, "Harus ada minimal satu owner aktif di tenant ini.")
            else:
                services.set_membership_access(
                    membership=membership,
                    role_code=new_role.code,
                    branches=list(form.cleaned_data["branches"]),
                )
                services.set_membership_status(membership=membership, status=new_status)
                record_audit(
                    action="membership.access_updated",
                    tenant=request.tenant,
                    user=request.user,
                    entity=membership,
                    after={"role": new_role.code, "status": new_status},
                    request=request,
                )
                messages.success(request, "Akses anggota diperbarui.")
                return redirect("team:list")
    else:
        form = MemberAccessForm(
            membership=membership,
            initial={"role": membership.role_id, "status": membership.status},
        )

    return render(
        request,
        "accounts/team/member_form.html",
        {"form": form, "membership": membership},
    )


@login_required
@require_tenant
@require_permission(Perm.TEAM_MANAGE)
@require_POST
def invitation_cancel(request, pk):
    invitation = get_object_or_404(Invitation, pk=pk, tenant=request.tenant)
    services.cancel_invitation(invitation=invitation)
    record_audit(
        action="invitation.cancelled",
        tenant=request.tenant,
        user=request.user,
        entity=invitation,
        request=request,
    )
    messages.success(request, "Undangan dibatalkan.")
    return redirect("team:list")
