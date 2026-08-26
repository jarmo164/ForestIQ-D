"""Membership-scoped REST permissions and object-level data authorization."""
from __future__ import annotations

from rest_framework.permissions import BasePermission

from accounts.models import PrivilegeCode
from accounts.organization_context import current_organization_id


def current_membership(subject):
    """Return the request-bound membership, never a global role assignment."""
    return getattr(subject, "organization_membership", None)


def has_membership_privilege(subject, *codes: str) -> bool:
    """Evaluate permissions only in the authenticated organization context."""
    user = getattr(subject, "user", subject)
    membership = current_membership(subject)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if membership is None or current_organization_id() is None:
        return False
    return bool(user.is_superuser or membership.has_privilege(*codes))


class HasOrganizationMembership(BasePermission):
    """Require a verified, active organization membership with any known role."""

    def has_permission(self, request, view) -> bool:
        membership = current_membership(request)
        return bool(
            request.user
            and request.user.is_authenticated
            and current_organization_id() is not None
            and membership is not None
            and membership.role_codes
        )


class HasForestIQPrivilege(HasOrganizationMembership):
    """Permission base class for tenant-scoped ForestIQ privilege sets."""

    required_privileges: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        return super().has_permission(request, view) and has_membership_privilege(request, *self.required_privileges)


class CanViewOrganizationData(HasOrganizationMembership):
    """Read-only information available to any explicitly assigned organization role."""


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


def can_access_owner(subject, owner) -> bool:
    """Enforce CRM-wide versus caller-assigned owner data access inside one tenant."""
    user = getattr(subject, "user", subject)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    if has_membership_privilege(subject, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        return True
    return has_membership_privilege(subject, PrivilegeCode.ASSIGNED_OWNERS) and owner.assignee_id == user.id
