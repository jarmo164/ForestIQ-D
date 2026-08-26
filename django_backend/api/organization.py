"""Helpers for organization-bound API object lookup and user selection."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from accounts.models import User
from accounts.organization_context import current_organization_id


def request_organization_id(request):
    """Return the trusted token/task organization, never a caller-supplied value."""

    organization_id = getattr(request, "organization_id", None) or current_organization_id()
    if organization_id is None:
        raise PermissionDenied("An organization context is required.")
    return organization_id


def organization_users(request, *, active_only: bool = False):
    """Return only users who belong to the authenticated organization."""

    queryset = User.objects.filter(organization_memberships__organization_id=request_organization_id(request)).distinct()
    return queryset.filter(is_active=True) if active_only else queryset


def organization_user_or_404(request, user_id: str, *, active_only: bool = False) -> User:
    """Resolve a user only if that user belongs to the authenticated organization."""

    queryset = organization_users(request, active_only=active_only)
    return get_object_or_404(queryset, id=user_id)
