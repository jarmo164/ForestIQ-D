"""Domain-level REST permissions."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from accounts.models import PrivilegeCode
from accounts.organization_context import current_organization_id


class HasForestIQPrivilege(BasePermission):
    """Permission base class for an explicit ForestIQ privilege set."""

    required_privileges: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and current_organization_id() is not None
            and request.user.has_privilege(*self.required_privileges)
        )


class IsAdmin(HasForestIQPrivilege):
    required_privileges = (PrivilegeCode.ADMIN,)


class CanManageOwners(HasForestIQPrivilege):
    required_privileges = (PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE, PrivilegeCode.ASSIGNED_OWNERS)


class CanUseAssignedOwners(HasForestIQPrivilege):
    required_privileges = (PrivilegeCode.ADMIN, PrivilegeCode.ASSIGNED_OWNERS)


class CanEvaluate(HasForestIQPrivilege):
    required_privileges = (PrivilegeCode.ADMIN, PrivilegeCode.EVALUATION)


class CanUsePhones(HasForestIQPrivilege):
    required_privileges = (PrivilegeCode.ADMIN, PrivilegeCode.PHONES)


def can_access_owner(user, owner) -> bool:
    """Apply the old ASSIGNED_OWNERS(*) ownership restriction."""
    if user.is_superuser or user.has_privilege(PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        return True
    return user.has_privilege(PrivilegeCode.ASSIGNED_OWNERS) and owner.assignee_id == user.id
