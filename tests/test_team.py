"""Team & access: invitations, role/branch assignment and the last-owner guard."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Invitation, Membership, MembershipStatus
from apps.accounts.roles import RoleCode
from apps.accounts.services import create_membership, invite_staff

User = get_user_model()


def _role(tenant, code):
    from apps.accounts.models import Role

    return Role.objects.get(tenant=tenant, code=code)


# ------------------------------------------------------------------ list ----


@pytest.mark.django_db
def test_owner_can_open_team_page(client, owner):
    client.force_login(owner)
    assert client.get(reverse("team:list")).status_code == 200


@pytest.mark.django_db
def test_cashier_cannot_manage_team(client, cashier):
    client.force_login(cashier)
    assert client.get(reverse("team:list")).status_code == 403


# -------------------------------------------------------------- inviting ----


@pytest.mark.django_db
def test_inviting_new_email_creates_invitation_and_sends_email(client, owner, tenant):
    client.force_login(owner)
    role = _role(tenant, RoleCode.CASHIER)

    response = client.post(
        reverse("team:invite"),
        {"email": "Baru@Example.com", "role": role.pk},
    )

    assert response.status_code == 302
    invitation = Invitation.objects.get(tenant=tenant)
    assert invitation.email == "baru@example.com"
    assert invitation.role == role
    assert invitation.status == MembershipStatus.INVITED
    assert len(mail.outbox) == 1
    assert invitation.token.hex[:8] in mail.outbox[0].body


@pytest.mark.django_db
def test_inviting_existing_account_adds_membership_immediately(client, owner, tenant):
    existing = User.objects.create_user(
        email="sudah@example.com", password="pass12345", name="Sudah Ada"
    )
    client.force_login(owner)
    role = _role(tenant, RoleCode.KITCHEN)

    response = client.post(
        reverse("team:invite"), {"email": "sudah@example.com", "role": role.pk}
    )

    assert response.status_code == 302
    assert not Invitation.objects.filter(tenant=tenant).exists()
    membership = Membership.objects.get(tenant=tenant, user=existing)
    assert membership.role == role
    assert membership.status == MembershipStatus.ACTIVE
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_invite_service_assigns_branches(tenant, branch, owner):
    membership, invitation = invite_staff(
        tenant=tenant,
        email="baru@example.com",
        role_code=RoleCode.CASHIER,
        branches=[branch],
        actor=owner,
    )

    assert membership is None
    assert list(invitation.branches.all()) == [branch]


# --------------------------------------------------------- member access ----


@pytest.mark.django_db
def test_owner_can_change_member_role_branches_and_status(
    client, owner, tenant, branch, cashier
):
    membership = Membership.objects.get(tenant=tenant, user=cashier)
    client.force_login(owner)
    manager_role = _role(tenant, RoleCode.MANAGER)

    response = client.post(
        reverse("team:member_edit", args=[membership.pk]),
        {"role": manager_role.pk, "branches": [branch.pk], "status": MembershipStatus.ACTIVE},
    )

    assert response.status_code == 302
    membership.refresh_from_db()
    assert membership.role.code == RoleCode.MANAGER
    assert [link.branch_id for link in membership.branch_memberships.all()] == [branch.pk]


@pytest.mark.django_db
def test_last_owner_cannot_be_demoted(client, owner, tenant):
    membership = Membership.objects.get(tenant=tenant, user=owner)
    client.force_login(owner)
    manager_role = _role(tenant, RoleCode.MANAGER)

    response = client.post(
        reverse("team:member_edit", args=[membership.pk]),
        {"role": manager_role.pk, "status": MembershipStatus.SUSPENDED},
        follow=True,
    )

    membership.refresh_from_db()
    assert membership.role.code == RoleCode.OWNER
    assert membership.status == MembershipStatus.ACTIVE
    assert "minimal satu owner aktif" in response.content.decode()


@pytest.mark.django_db
def test_owner_can_cancel_invitation(client, owner, tenant):
    _membership, invitation = invite_staff(
        tenant=tenant, email="batal@example.com", role_code=RoleCode.CASHIER, actor=owner
    )
    client.force_login(owner)

    response = client.post(reverse("team:invitation_cancel", args=[invitation.pk]))

    assert response.status_code == 302
    invitation.refresh_from_db()
    assert invitation.status == MembershipStatus.REVOKED


# ------------------------------------------------------ accepting by link ----


@pytest.mark.django_db
def test_new_invitee_sets_password_and_joins(client, tenant, owner, branch):
    _membership, invitation = invite_staff(
        tenant=tenant,
        email="baru@example.com",
        role_code=RoleCode.CASHIER,
        branches=[branch],
        actor=owner,
    )

    response = client.post(
        reverse("accounts:invitation_accept", args=[invitation.token]),
        {"name": "Staf Baru", "password1": "rahasia12345", "password2": "rahasia12345"},
    )

    assert response.status_code == 302
    user = User.objects.get(email="baru@example.com")
    assert user.check_password("rahasia12345")
    membership = Membership.objects.get(tenant=tenant, user=user)
    assert membership.status == MembershipStatus.ACTIVE
    assert [link.branch_id for link in membership.branch_memberships.all()] == [branch.pk]

    invitation.refresh_from_db()
    assert invitation.status == MembershipStatus.ACTIVE
    assert invitation.accepted_at is not None


@pytest.mark.django_db
def test_expired_invitation_is_rejected(client, tenant, owner):
    _membership, invitation = invite_staff(
        tenant=tenant, email="telat@example.com", role_code=RoleCode.CASHIER, actor=owner
    )
    invitation.expires_at = timezone.now() - timedelta(hours=1)
    invitation.save(update_fields=["expires_at"])

    response = client.get(reverse("accounts:invitation_accept", args=[invitation.token]))

    assert response.status_code == 200
    assert "Undangan tidak berlaku" in response.content.decode()
    assert not User.objects.filter(email="telat@example.com").exists()


def _pending_invitation(tenant, email, code):
    """An invitation for an address that already has an account.

    `invite_staff` adds existing accounts directly, but this state is reachable
    in real life when the invitee registers before opening the link.
    """
    return Invitation.objects.create(
        tenant=tenant,
        email=email,
        role=_role(tenant, code),
        expires_at=timezone.now() + timedelta(days=7),
    )


@pytest.mark.django_db
def test_existing_account_must_sign_in_before_accepting(client, tenant, owner):
    User.objects.create_user(email="ada@example.com", password="pass12345", name="Ada")
    invitation = _pending_invitation(tenant, "ada@example.com", RoleCode.CASHIER)

    response = client.get(reverse("accounts:invitation_accept", args=[invitation.token]))

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]
    invitation.refresh_from_db()
    assert invitation.status == MembershipStatus.INVITED


@pytest.mark.django_db
def test_signed_in_existing_account_accepts(client, tenant, owner):
    user = User.objects.create_user(
        email="ada@example.com", password="pass12345", name="Ada"
    )
    invitation = _pending_invitation(tenant, "ada@example.com", RoleCode.MANAGER)
    client.force_login(user)

    response = client.post(reverse("accounts:invitation_accept", args=[invitation.token]))

    assert response.status_code == 302
    membership = Membership.objects.get(tenant=tenant, user=user)
    assert membership.role.code == RoleCode.MANAGER
    assert membership.status == MembershipStatus.ACTIVE


@pytest.mark.django_db
def test_manager_without_team_permission_cannot_invite(client, tenant, branch):
    user = User.objects.create_user(email="mgr2@example.com", password="pass12345", name="Mgr")
    create_membership(tenant=tenant, user=user, role_code=RoleCode.MANAGER, branches=[branch])
    client.force_login(user)

    assert client.get(reverse("team:invite")).status_code == 403
