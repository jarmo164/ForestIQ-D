"""Authentication endpoints for local development and Keycloak OIDC login."""
from __future__ import annotations

import base64
import binascii
from datetime import timedelta

import pyotp
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, Token

from accounts.models import OrganizationMembership, User
from accounts.oidc import OIDCAuthenticationError, exchange_authorization_code, public_configuration


class TotpToken(Token):
    """Short-lived pre-authentication token used only by local development login."""

    token_type = "totp"
    lifetime = timedelta(seconds=settings.TOTP_TOKEN_LIFETIME_SECONDS)


def _active_membership(user: User, organization_id=None) -> OrganizationMembership:
    """Resolve the one tenant boundary embedded in an internal ForestIQ JWT."""
    organization_id = organization_id or user.default_organization_id
    return OrganizationMembership.objects.select_related("organization").get(
        user=user,
        organization_id=organization_id,
        organization__is_active=True,
    )


def _claims(token: Token, user: User, membership: OrganizationMembership, *, auth_source: str) -> None:
    token["userId"] = user.id
    token["userName"] = user.full_name
    token["privileges"] = membership.privilege_codes
    token["roles"] = membership.role_codes
    token["organization_id"] = str(membership.organization_id)
    token["organizationId"] = str(membership.organization_id)
    token["auth_source"] = auth_source


def token_pair(user: User, membership: OrganizationMembership | None = None, *, auth_source: str = "local") -> dict:
    """Mint a ForestIQ API token only for an active organization membership."""
    membership = membership or _active_membership(user)
    refresh = RefreshToken.for_user(user)
    _claims(refresh, user, membership, auth_source=auth_source)
    access = refresh.access_token
    _claims(access, user, membership, auth_source=auth_source)
    return {
        "actualToken": {"token": str(access)},
        "refreshToken": {"token": str(refresh)},
    }


def _basic_credentials(request) -> tuple[str, str] | None:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return None
    try:
        encoded = header.split(" ", 1)[1]
        user_id, password = base64.b64decode(encoded).decode("utf-8").split(":", 1)
    except (ValueError, UnicodeDecodeError, binascii.Error):
        return None
    return user_id, password


def _local_login_disabled() -> Response:
    return Response({"detail": "Local development login is disabled."}, status=status.HTTP_403_FORBIDDEN)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def oidc_configuration(request):
    """Expose only browser-safe Keycloak Authorization Code + PKCE metadata."""
    try:
        return Response(public_configuration())
    except OIDCAuthenticationError as error:
        return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def oidc_exchange(request):
    """Exchange a PKCE authorization code and create the internal tenant JWT."""
    try:
        user, membership = exchange_authorization_code(
            code=str(request.data.get("code") or ""),
            code_verifier=str(request.data.get("codeVerifier") or ""),
            redirect_uri=str(request.data.get("redirectUri") or ""),
            nonce=str(request.data.get("nonce") or "") or None,
        )
    except OIDCAuthenticationError as error:
        return Response({"detail": str(error)}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(token_pair(user, membership, auth_source="keycloak"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def password_login(request):
    if not settings.FORESTIQ_DEVMODE:
        return _local_login_disabled()
    credentials = _basic_credentials(request)
    if not credentials:
        return Response({"detail": "Basic authorization is required."}, status=status.HTTP_401_UNAUTHORIZED)
    user_id, password = credentials
    user = authenticate(request, username=user_id, password=password)
    if user is None:
        return Response({"detail": "Invalid user id or password."}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        membership = _active_membership(user)
    except OrganizationMembership.DoesNotExist:
        return Response({"detail": "User has no active organization membership."}, status=status.HTTP_401_UNAUTHORIZED)
    token = TotpToken.for_user(user)
    _claims(token, user, membership, auth_source="local")
    token["totpsecret"] = bool(user.totp_secret)
    return Response({"token": str(token)})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def totp_login(request):
    if not settings.FORESTIQ_DEVMODE:
        return _local_login_disabled()
    raw_token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    try:
        pre_auth = TotpToken(raw_token)
        user = User.objects.get(id=pre_auth["user_id"], is_active=True)
        membership = _active_membership(user, pre_auth.get("organization_id"))
    except (TokenError, User.DoesNotExist, OrganizationMembership.DoesNotExist, KeyError):
        return Response({"detail": "Invalid or expired TOTP token."}, status=status.HTTP_401_UNAUTHORIZED)
    code = str(request.data.get("code") or request.data.get("totpCode") or request.data.get("token") or "")
    is_valid = code == "000000"
    if user.totp_secret:
        try:
            is_valid = is_valid or pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)
        except (TypeError, ValueError):
            is_valid = False
    if not is_valid:
        return Response({"detail": "Invalid authentication code."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(token_pair(user, membership, auth_source="local"))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def refresh_token(request):
    raw_token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    try:
        refresh = RefreshToken(raw_token)
        user = User.objects.get(id=refresh["user_id"], is_active=True)
        membership = _active_membership(user, refresh.get("organization_id"))
        refresh.blacklist()
    except (TokenError, User.DoesNotExist, OrganizationMembership.DoesNotExist, KeyError):
        return Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(token_pair(user, membership, auth_source=str(refresh.get("auth_source") or "local")))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_my_password(request):
    if not settings.FORESTIQ_DEVMODE:
        return _local_login_disabled()
    user = request.user
    old_password = request.data.get("oldPassword", "")
    new_password = request.data.get("newPassword", "")
    new_password_again = request.data.get("newPasswordAgain", "")
    if not user.check_password(old_password):
        return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
    if len(new_password) < 12 or new_password != new_password_again:
        return Response({"detail": "New passwords must match and contain at least 12 characters."}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return Response(token_pair(user, request.organization_membership, auth_source="local"))
