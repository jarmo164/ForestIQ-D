"""Bridge legacy ForestIQ privilege rows to Django Groups and permissions."""

from __future__ import annotations

from django.contrib.auth.models import Group

from accounts.models import OrganizationMembership, PrivilegeCode, User, roles_from_legacy_privileges

ROLE_GROUPS = {
    PrivilegeCode.ADMIN: "ForestIQ Administrators",
    PrivilegeCode.OWNER_PROFILE: "ForestIQ Owner Profiles",
    PrivilegeCode.ASSIGNED_OWNERS: "ForestIQ Assigned Owners",
    PrivilegeCode.PHONES: "ForestIQ Phone Directory",
    PrivilegeCode.EVALUATION: "ForestIQ Evaluators",
}


def sync_user_groups(user: User) -> None:
    """Synchronise managed Django groups from stable legacy privilege codes."""
    managed_names = list(ROLE_GROUPS.values())
    granted = set(user.privilege_assignments.values_list("code", flat=True))
    wanted_names = [name for code, name in ROLE_GROUPS.items() if code in granted]
    wanted_groups = [Group.objects.get_or_create(name=name)[0] for name in wanted_names]
    user.groups.remove(*Group.objects.filter(name__in=managed_names))
    user.groups.add(*wanted_groups)

    # Local users remain supported only in development. Keep their tenant roles
    # equivalent to the legacy privileges while never overwriting Keycloak state.
    local_memberships = OrganizationMembership.objects.filter(user=user, oidc_managed=False)
    local_memberships.update(roles=roles_from_legacy_privileges(granted))
