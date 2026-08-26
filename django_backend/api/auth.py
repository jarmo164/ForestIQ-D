"""Authentication endpoints compatible with the existing ForestIQ browser client."""

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
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken, Token

from accounts.models import User


class TotpToken(Token):
    """Short-lived pre-authentication token used only by the TOTP endpoint."""

    token_type = "totp"
    lifetime = timedelta(seconds=settings.TOTP_TOKEN_LIFETIME_SECONDS)


def _claims(token: Token, user: User) -> None:
    token["userId"] = user.id
    token["userName"] = user.full_name
    token["privileges"] = user.privilege_codes
    token["organization_id"] = str(user.default_organization_id)
    token["organizationId"] = str(user.default_organization_id)


def token_pair(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    _claims(refresh, user)
    access = refresh.access_token
    _claims(access, user)
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


@api_view(["POST"])
@permission_classes([AllowAny])
def password_login(request):
    credentials = _basic_credentials(request)
    if not credentials:
        return Response({"detail": "Basic authorization is required."}, status=status.HTTP_401_UNAUTHORIZED)
    user_id, password = credentials
    user = authenticate(request, username=user_id, password=password)
    if user is None:
        return Response({"detail": "Invalid user id or password."}, status=status.HTTP_401_UNAUTHORIZED)

    token = TotpToken.for_user(user)
    _claims(token, user)
    token["totpsecret"] = bool(user.totp_secret)
    return Response({"token": str(token)})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def totp_login(request):
    raw_token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    try:
        pre_auth = TotpToken(raw_token)
        user = User.objects.get(id=pre_auth["user_id"], is_active=True)
    except (TokenError, User.DoesNotExist, KeyError):
        return Response({"detail": "Invalid or expired TOTP token."}, status=status.HTTP_401_UNAUTHORIZED)

    code = str(request.data.get("code") or request.data.get("totpCode") or request.data.get("token") or "")
    is_valid = settings.FORESTIQ_DEVMODE and code == "000000"
    if user.totp_secret:
        try:
            is_valid = is_valid or pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)
        except (TypeError, ValueError):
            is_valid = False
    if not is_valid:
        return Response({"detail": "Invalid authentication code."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(token_pair(user))


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def refresh_token(request):
    raw_token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    try:
        refresh = RefreshToken(raw_token)
        user = User.objects.get(id=refresh["user_id"], is_active=True)
        refresh.blacklist()
    except (TokenError, User.DoesNotExist, KeyError):
        return Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(token_pair(user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_my_password(request):
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
    return Response(token_pair(user))
