"""JWT authentication that binds every authenticated API request to one organization."""

from __future__ import annotations

from uuid import UUID

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from accounts.models import OrganizationMembership
from accounts.organization_context import activate_organization


class OrganizationJWTAuthentication(JWTAuthentication):
    """Reject tokens without an active membership and activate their organization scope."""

    def authenticate(self, request):
        authenticated = super().authenticate(request)
        if authenticated is None:
            return None

        user, token = authenticated
        raw_organization_id = token.get("organization_id")
        try:
            organization_id = UUID(str(raw_organization_id))
        except (TypeError, ValueError):
            raise AuthenticationFailed("JWT does not contain a valid organization_id claim.")

        membership_exists = OrganizationMembership.objects.filter(
            user_id=user.id,
            organization_id=organization_id,
            organization__is_active=True,
        ).exists()
        if not membership_exists:
            raise AuthenticationFailed("JWT organization is not an active membership for this user.")

        context_token = activate_organization(organization_id)
        request._forestiq_organization_context_token = context_token
        raw_request = getattr(request, "_request", None)
        if raw_request is not None:
            raw_request._forestiq_organization_context_token = context_token
        request.organization_id = organization_id
        if raw_request is not None:
            raw_request.organization_id = organization_id
        return user, token
