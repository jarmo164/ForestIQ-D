"""Identity and privilege models for the ForestIQ domain."""

from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


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
