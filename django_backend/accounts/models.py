"""Identity and privilege models for the ForestIQ domain."""

from __future__ import annotations

import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models

from accounts.organization_context import OrganizationScopedManager, current_organization_id


DEFAULT_ORGANIZATION_SLUG = "forestiq-default"
DEFAULT_ORGANIZATION_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


class Organization(models.Model):
    """A hard ownership boundary for every ForestIQ business record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=180, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "organizations"
        ordering = ("name", "id")

    def __str__(self) -> str:
        return self.name


def default_organization_id():
    """Return the legacy organization used during the staged tenancy rollout."""

    return DEFAULT_ORGANIZATION_ID


class OrganizationScopedModel(models.Model):
    """Base model that persists the ownership boundary on each business row."""

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="+",
        default=default_organization_id,
    )
    organization_parent_fields: tuple[str, ...] = ()
    objects = OrganizationScopedManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        default_manager_name = "objects"
        base_manager_name = "all_objects"

    def save(self, *args, **kwargs):
        """Keep dependent records in the same organization as their aggregate root."""

        active_organization_id = current_organization_id()
        if self._state.adding and active_organization_id and self.organization_id == DEFAULT_ORGANIZATION_ID:
            self.organization_id = active_organization_id
        parent_organization_ids = set()
        for parent_field in self.organization_parent_fields:
            parent = getattr(self, parent_field, None)
            parent_organization_id = getattr(parent, "organization_id", None)
            if parent_organization_id:
                parent_organization_ids.add(parent_organization_id)
        if len(parent_organization_ids) > 1:
            raise ValidationError("All aggregate parents must belong to the same organization.")
        if parent_organization_ids:
            self.organization_id = parent_organization_ids.pop()
        return super().save(*args, **kwargs)


class PrivilegeCode(models.TextChoices):
    ADMIN = "ADMIN", "Administrator"
    OWNER_PROFILE = "OWNER_PROFILE", "Owner profile"
    ASSIGNED_OWNERS = "ASSIGNED_OWNERS", "Assigned owners"
    PHONES = "PHONES", "Phone directory"
    EVALUATION = "EVALUATION", "Evaluation"


class UserManager(BaseUserManager):
    """Manager that uses the legacy human-readable identifier as the login name."""

    def create_user(self, user_id: str, full_name: str, password: str | None = None, **extra_fields):
        if not user_id:
            raise ValueError("User id is required")
        if not full_name:
            raise ValueError("Full name is required")
        user = self.model(id=user_id.strip(), full_name=full_name.strip(), **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id: str, full_name: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        user = self.create_user(user_id, full_name, password, **extra_fields)
        Privilege.objects.get_or_create(user=user, code=PrivilegeCode.ADMIN)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """ForestIQ application user with a stable string primary key."""

    id = models.CharField(primary_key=True, max_length=50)
    full_name = models.CharField(max_length=100, db_column="fullname")
    password = models.CharField("password hash", max_length=128, db_column="password_hash")
    totp_secret = models.CharField(max_length=64, blank=True, null=True)
    visible = models.BooleanField(default=False, db_column="ivisible")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    default_organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="default_users",
        default=default_organization_id,
    )
    organizations = models.ManyToManyField(Organization, through="OrganizationMembership", related_name="users")

    objects = UserManager()

    USERNAME_FIELD = "id"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "users"
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.id} ({self.full_name})"

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.full_name

    @property
    def organization_id(self):
        """Compatibility alias while AUTH-02 gains a request-bound context."""

        return self.default_organization_id

    @property
    def organization(self):
        return self.default_organization

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.default_organization_id:
            OrganizationMembership.objects.get_or_create(organization_id=self.default_organization_id, user_id=self.pk)

    @property
    def privilege_codes(self) -> list[str]:
        return list(self.privilege_assignments.values_list("code", flat=True))

    def has_privilege(self, *codes: str) -> bool:
        if self.is_superuser:
            return True
        granted = set(self.privilege_codes)
        return any(code in granted for code in codes)


class Privilege(models.Model):
    """One explicit domain privilege granted to a user."""

    id = models.BigAutoField(primary_key=True, db_column="pk")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="privilege_assignments", db_column="user_id")
    code = models.CharField(max_length=50, choices=PrivilegeCode.choices, db_column="id")

    class Meta:
        db_table = "privileges"
        constraints = [models.UniqueConstraint(fields=("user", "code"), name="unique_user_privilege")]
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.user_id}:{self.code}"


class OrganizationMembership(models.Model):
    """Explicit user-to-organization membership, ready for OIDC role mapping."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organization_memberships")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "organization_memberships"
        constraints = [models.UniqueConstraint(fields=("organization", "user"), name="unique_organization_membership")]
        indexes = [models.Index(fields=("user", "organization"), name="org_member_user_idx")]

    def __str__(self) -> str:
        return f"{self.organization.slug}:{self.user_id}"
