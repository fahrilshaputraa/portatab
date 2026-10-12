"""Identity/access domain services.

Single source of truth for role seeding, membership management and staff
invitations so onboarding, invitations and admin tools all share one code path.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import (
    BranchMembership,
    Invitation,
    Membership,
    MembershipStatus,
    Permission,
    Role,
    RolePermission,
)
from apps.accounts.roles import ALL_PERMISSIONS, SYSTEM_ROLES

User = get_user_model()

INVITATION_TTL_DAYS = 7


def ensure_permissions() -> None:
    """Create any permission that is registered in code but missing in the DB."""
    existing = set(Permission.objects.values_list("code", flat=True))
    Permission.objects.bulk_create(
        [
            Permission(code=code, description=desc)
            for code, desc in ALL_PERMISSIONS.items()
            if code not in existing
        ],
        ignore_conflicts=True,
    )


@transaction.atomic
def seed_system_roles(tenant) -> dict[str, Role]:
    """Create the tenant's copy of the system roles and their permissions."""
    ensure_permissions()
    perms = {p.code: p for p in Permission.objects.filter(code__in=ALL_PERMISSIONS)}

    roles: dict[str, Role] = {}
    for code, (name, perm_codes) in SYSTEM_ROLES.items():
        role, _ = Role.objects.get_or_create(
            tenant=tenant, code=code, defaults={"name": name, "is_system": True}
        )
        RolePermission.objects.bulk_create(
            [
                RolePermission(role=role, permission=perms[perm_code])
                for perm_code in perm_codes
                if perm_code in perms
            ],
            ignore_conflicts=True,
        )
        roles[code] = role
    return roles


@transaction.atomic
def create_membership(
    *,
    tenant,
    user,
    role_code: str,
    status: str = MembershipStatus.ACTIVE,
    branches=None,
) -> Membership:
    """Add (or update) a user's membership in a tenant, optionally scoping branches."""
    role = Role.objects.get(tenant=tenant, code=role_code)
    membership, _ = Membership.objects.get_or_create(
        tenant=tenant, user=user, defaults={"role": role, "status": status}
    )
    membership.role = role
    membership.status = status
    if status == MembershipStatus.ACTIVE and membership.joined_at is None:
        membership.joined_at = timezone.now()
    membership.save(update_fields=["role", "status", "joined_at"])

    for branch in branches or []:
        # A branch outside the tenant must never be granted.
        if branch.tenant_id != tenant.id:
            raise ValueError("Branch tidak berada di tenant yang sama.")
        BranchMembership.objects.get_or_create(membership=membership, branch=branch)

    return membership


# ---------------------------------------------------------------------------
# Team & access
# ---------------------------------------------------------------------------


def invitation_url(invitation, request=None) -> str:
    path = reverse("accounts:invitation_accept", args=[invitation.token])
    return request.build_absolute_uri(path) if request is not None else path


@transaction.atomic
def invite_staff(*, tenant, email: str, role_code: str, branches=None, actor=None):
    """Invite someone to the team.

    An existing account is added as an active member straight away; otherwise a
    pending invitation is created and returned for the caller to email.
    Returns ``(membership_or_None, invitation_or_None)``.
    """
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("Email wajib diisi.")

    role = Role.objects.get(tenant=tenant, code=role_code)
    user = User.objects.filter(email=email).first()

    if user is not None:
        membership = create_membership(
            tenant=tenant, user=user, role_code=role_code, branches=branches
        )
        return membership, None

    invitation, _ = Invitation.objects.update_or_create(
        tenant=tenant,
        email=email,
        status=MembershipStatus.INVITED,
        defaults={
            "role": role,
            "invited_by": actor,
            "expires_at": timezone.now() + timedelta(days=INVITATION_TTL_DAYS),
        },
    )
    invitation.branches.set(branches or [])
    return None, invitation


def send_invitation_email(*, invitation, request=None) -> int:
    """Email the invitation link. Uses whatever EMAIL_BACKEND is configured."""
    url = invitation_url(invitation, request)
    subject = f"Undangan bergabung ke {invitation.tenant.name} di PortaTap"
    body = (
        f"Halo,\n\n"
        f"{invitation.tenant.name} mengundang Anda bergabung sebagai "
        f"{invitation.role.name} di PortaTap.\n\n"
        f"Buka tautan berikut untuk mengaktifkan akses Anda:\n{url}\n\n"
        f"Tautan berlaku sampai {invitation.expires_at:%d %B %Y %H:%M}.\n\n"
        f"Kalau Anda tidak merasa diundang, abaikan email ini.\n"
    )
    return send_mail(subject, body, None, [invitation.email], fail_silently=False)


@transaction.atomic
def accept_invitation(*, invitation, name: str = "", password: str | None = None):
    """Activate a pending invitation, creating the account when needed."""
    if invitation.status != MembershipStatus.INVITED:
        raise ValueError("Undangan ini sudah tidak aktif.")
    if invitation.expires_at <= timezone.now():
        raise ValueError("Undangan ini sudah kedaluwarsa.")

    email = invitation.email.lower()
    user = User.objects.filter(email=email).first()
    if user is None:
        if not password:
            raise ValueError("Kata sandi wajib diisi untuk akun baru.")
        user = User.objects.create_user(
            email=email, password=password, name=name.strip() or email.split("@")[0]
        )

    membership = create_membership(
        tenant=invitation.tenant,
        user=user,
        role_code=invitation.role.code,
        branches=list(invitation.branches.all()),
    )
    invitation.status = MembershipStatus.ACTIVE
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=["status", "accepted_at"])
    return user, membership


@transaction.atomic
def set_membership_access(*, membership, role_code: str, branches=None) -> Membership:
    """Change a member's role and exactly which branches they may operate on."""
    role = Role.objects.get(tenant=membership.tenant, code=role_code)
    membership.role = role
    membership.save(update_fields=["role"])

    wanted = list(branches or [])
    BranchMembership.objects.filter(membership=membership).exclude(branch__in=wanted).delete()
    for branch in wanted:
        if branch.tenant_id != membership.tenant_id:
            raise ValueError("Branch tidak berada di tenant yang sama.")
        BranchMembership.objects.get_or_create(membership=membership, branch=branch)
    return membership


def set_membership_status(*, membership, status: str) -> Membership:
    """Activate, suspend or revoke a membership."""
    membership.status = status
    if status == MembershipStatus.ACTIVE and membership.joined_at is None:
        membership.joined_at = timezone.now()
    membership.save(update_fields=["status", "joined_at"])
    return membership


def cancel_invitation(*, invitation) -> Invitation:
    invitation.status = MembershipStatus.REVOKED
    invitation.save(update_fields=["status"])
    return invitation
