"""Identity, membership and access control.

This app owns:

- ``User``          — the single account used by owners, staff and platform admins.
- ``Role`` / ``Permission`` — tenant-scoped roles and their granted permissions.
- ``Membership``    — a user's role inside one tenant (a user may join many).
- ``BranchMembership`` — which branches a membership may operate on.
- ``Invitation``    — pending staff invitations.

Authorization is always enforced server-side (docs/BUSINESS-RULES.md §2); these
models only supply the data the checks read.
"""

import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDModel


class UserStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Aktif"
    INACTIVE = "INACTIVE", "Nonaktif"
    SUSPENDED = "SUSPENDED", "Ditangguhkan"


class MembershipStatus(models.TextChoices):
    INVITED = "INVITED", "Diundang"
    ACTIVE = "ACTIVE", "Aktif"
    SUSPENDED = "SUSPENDED", "Ditangguhkan"
    REVOKED = "REVOKED", "Dicabut"


class UserManager(BaseUserManager):
    """Manager for the email-first custom user model."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email wajib diisi.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("status", UserStatus.ACTIVE)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields.get("is_staff") or not extra_fields.get("is_superuser"):
            raise ValueError("Superuser harus punya is_staff dan is_superuser True.")
        return self._create_user(email, password, **extra_fields)


class User(UUIDModel, AbstractBaseUser, PermissionsMixin):
    """A person who can sign in.

    One account may hold memberships in several tenants (docs/ERD.md). Platform
    administration is expressed with ``is_staff`` / ``is_superuser`` and is
    separate from tenant ownership (docs/BUSINESS-RULES.md §2).
    """

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    status = models.CharField(
        max_length=16, choices=UserStatus.choices, default=UserStatus.ACTIVE, db_index=True
    )
    email_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    is_staff = models.BooleanField(
        default=False,
        help_text="Boleh mengakses portal administrasi platform.",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        ordering = ["name", "email"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

    def get_full_name(self) -> str:
        return self.name

    def get_short_name(self) -> str:
        return self.name.split(" ")[0] if self.name else self.email

    @property
    def is_active(self) -> bool:
        """Derived from ``status`` so there is a single source of truth."""
        return self.status == UserStatus.ACTIVE

    def mark_login(self) -> None:
        self.last_login_at = timezone.now()
        self.save(update_fields=["last_login_at", "updated_at"])


class Permission(UUIDModel):
    """A named capability, e.g. ``orders.accept``.

    Permissions are global definitions; roles grant them per tenant.
    """

    code = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code


class Role(UUIDModel):
    """A tenant-scoped set of permissions assigned to memberships."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="roles"
    )
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64)
    is_system = models.BooleanField(
        default=False, help_text="Role bawaan yang tidak boleh dihapus tenant."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "code"], name="uniq_role_tenant_code"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant_id})"


class RolePermission(UUIDModel):
    """Grants one permission to one role."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="role_permissions"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"], name="uniq_role_permission"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.role.code}:{self.permission.code}"


class Membership(UUIDModel):
    """A user's role inside one tenant."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="memberships"
    )
    status = models.CharField(
        max_length=16,
        choices=MembershipStatus.choices,
        default=MembershipStatus.INVITED,
        db_index=True,
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["tenant_id", "user_id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "user"], name="uniq_membership_tenant_user"),
        ]
        indexes = [models.Index(fields=["tenant", "status"])]

    def __str__(self) -> str:
        return f"{self.user_id}@{self.tenant_id} ({self.status})"

    @property
    def is_active(self) -> bool:
        return self.status == MembershipStatus.ACTIVE

    def activate(self) -> None:
        self.status = MembershipStatus.ACTIVE
        self.joined_at = self.joined_at or timezone.now()
        self.save(update_fields=["status", "joined_at"])

    def has_permission(self, code: str) -> bool:
        """True when the member's role grants ``code``."""
        return self.role.role_permissions.filter(permission__code=code).exists()


class BranchMembership(UUIDModel):
    """Grants a membership access to a specific branch."""

    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="branch_memberships"
    )
    branch = models.ForeignKey(
        "tenants.Branch", on_delete=models.CASCADE, related_name="branch_memberships"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "branch"], name="uniq_branch_membership"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.membership_id}@{self.branch_id}"


class Invitation(UUIDModel):
    """A pending invitation for a staff member to join a tenant."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="invitations")
    branches = models.ManyToManyField(
        "tenants.Branch", related_name="invitations", blank=True
    )
    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sent_invitations"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(
        max_length=16, choices=MembershipStatus.choices, default=MembershipStatus.INVITED
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.email} -> {self.tenant_id}"
