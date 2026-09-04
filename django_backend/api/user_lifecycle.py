"""Keycloak-backed administrator user lifecycle with deletion-impact protection."""

from __future__ import annotations

import os
from urllib.parse import quote

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import OrganizationMembership, OrganizationRole, User, normalize_organization_roles
from forestry.models import Owner, OwnerFollowing, OwnerLog
from operations.models import Deal, DealStage, InheritanceCase, Reminder

from .organization import request_organization_id
from .permissions import IsAdmin


class KeycloakAdminError(RuntimeError):
    pass


def _detail(message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> Response:
    return Response({"detail": message}, status=http_status)


def _keycloak_admin_config() -> tuple[str, str, str, str]:
    issuer = settings.KEYCLOAK_ISSUER.rstrip("/")
    if not settings.KEYCLOAK_OIDC_ENABLED or "/realms/" not in issuer:
        raise KeycloakAdminError("Keycloak OIDC is not configured.")
    root, realm = issuer.rsplit("/realms/", 1)
    client_id = os.getenv("KEYCLOAK_ADMIN_CLIENT_ID", "forestiq-admin").strip()
    client_secret = os.getenv("KEYCLOAK_ADMIN_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise KeycloakAdminError("KEYCLOAK_ADMIN_CLIENT_ID and KEYCLOAK_ADMIN_CLIENT_SECRET are required.")
    return issuer, f"{root}/admin/realms/{realm}", client_id, client_secret


def _admin_token() -> tuple[str, str]:
    issuer, admin_base, client_id, client_secret = _keycloak_admin_config()
    try:
        response = requests.post(
            f"{issuer}/protocol/openid-connect/token",
            data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
            timeout=settings.KEYCLOAK_HTTP_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise KeycloakAdminError(f"Keycloak admin token request failed: {exc}") from exc
    if response.status_code >= 400:
        raise KeycloakAdminError(f"Keycloak admin token request failed ({response.status_code}).")
    token = str(response.json().get("access_token") or "")
    if not token:
        raise KeycloakAdminError("Keycloak admin token response did not contain access_token.")
    return admin_base, token


def _kc_request(method: str, path: str, *, json=None, expected=(200, 201, 204)) -> requests.Response:
    admin_base, token = _admin_token()
    try:
        response = requests.request(
            method,
            f"{admin_base}{path}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            json=json,
            timeout=settings.KEYCLOAK_HTTP_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise KeycloakAdminError(f"Keycloak admin request failed: {exc}") from exc
    if response.status_code not in expected:
        raise KeycloakAdminError(f"Keycloak admin request failed ({response.status_code}): {response.text[:300]}")
    return response


def _keycloak_user_id(user: User) -> str:
    if user.oidc_subject:
        return user.oidc_subject
    response = _kc_request("GET", f"/users?username={quote(user.id)}&exact=true")
    matches = response.json()
    if not matches:
        raise KeycloakAdminError(f"Keycloak user {user.id} was not found.")
    return str(matches[0]["id"])


def _role_representations(roles: list[str]) -> list[dict]:
    representations = []
    for role in roles:
        response = _kc_request("GET", f"/roles/{quote(role)}")
        representations.append(response.json())
    return representations


def _replace_keycloak_roles(keycloak_user_id: str, roles: list[str]) -> None:
    current = _kc_request("GET", f"/users/{keycloak_user_id}/role-mappings/realm").json()
    managed = [role for role in current if role.get("name") in set(OrganizationRole.values)]
    if managed:
        _kc_request("DELETE", f"/users/{keycloak_user_id}/role-mappings/realm", json=managed)
    if roles:
        _kc_request("POST", f"/users/{keycloak_user_id}/role-mappings/realm", json=_role_representations(roles))


def _deletion_impact(user: User) -> dict[str, int]:
    active_deal_stages = (DealStage.QUALIFICATION, DealStage.EVALUATION, DealStage.NEGOTIATION)
    active_inheritance = (InheritanceCase.Status.NEW, InheritanceCase.Status.IN_PROGRESS, InheritanceCase.Status.WAITING)
    return {
        "activeWork": Owner.objects.filter(assignee=user).count(),
        "activeDeals": Deal.objects.filter(Q(created_by=user) | Q(evaluator=user), stage__in=active_deal_stages).distinct().count(),
        "activeInheritances": InheritanceCase.objects.filter(assigned_to=user, status__in=active_inheritance).count(),
        "followings": OwnerFollowing.objects.filter(user=user).count(),
        "activeReminders": Reminder.objects.filter(creator=user, due_time__gte=timezone.now()).count(),
        "ownerLogs": OwnerLog.objects.filter(creator=user).count(),
    }


def _has_blockers(impact: dict[str, int]) -> bool:
    return any(value > 0 for value in impact.values())


@extend_schema(exclude=True)
@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_user_create(request):
    user_id = str(request.data.get("userId") or request.data.get("username") or "").strip()
    full_name = str(request.data.get("fullName") or "").strip()
    email = str(request.data.get("email") or "").strip()
    roles = normalize_organization_roles(request.data.get("roles") or [OrganizationRole.MEMBER])
    organization_id = request_organization_id(request)
    if not user_id or not full_name:
        return _detail("userId and fullName are required.")
    if not roles:
        return _detail("At least one recognized organization role is required.")
    if User.objects.filter(id=user_id).exists():
        return _detail("User already exists.", status.HTTP_409_CONFLICT)

    keycloak_id = None
    payload = {
        "username": user_id,
        "enabled": True,
        "firstName": full_name,
        "attributes": {settings.KEYCLOAK_ORGANIZATION_CLAIM: [str(organization_id)]},
    }
    if email:
        payload["email"] = email
    try:
        response = _kc_request("POST", "/users", json=payload)
        location = response.headers.get("Location", "")
        keycloak_id = location.rstrip("/").split("/")[-1] if location else ""
        if not keycloak_id:
            matches = _kc_request("GET", f"/users?username={quote(user_id)}&exact=true").json()
            keycloak_id = str(matches[0]["id"]) if matches else ""
        if not keycloak_id:
            raise KeycloakAdminError("Keycloak did not return the created user id.")
        _replace_keycloak_roles(keycloak_id, roles)
        with transaction.atomic():
            user = User.objects.create_user(
                user_id=user_id,
                full_name=full_name,
                oidc_subject=keycloak_id,
                default_organization_id=organization_id,
            )
            membership, _ = OrganizationMembership.objects.get_or_create(organization_id=organization_id, user=user)
            membership.set_roles(roles, oidc_managed=True)
    except KeycloakAdminError as exc:
        if keycloak_id:
            try:
                _kc_request("DELETE", f"/users/{keycloak_id}")
            except KeycloakAdminError:
                pass
        return _detail(str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response(
        {"id": user.id, "fullName": user.full_name, "oidcSubject": user.oidc_subject, "roles": membership.role_codes},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(exclude=True)
@api_view(["PUT"])
@permission_classes([IsAdmin])
def admin_user_roles(request, user_id: str):
    organization_id = request_organization_id(request)
    user = User.objects.filter(id=user_id, organization_memberships__organization_id=organization_id).distinct().first()
    if user is None:
        return _detail("User not found.", status.HTTP_404_NOT_FOUND)
    roles = normalize_organization_roles(request.data.get("roles") or [])
    if not roles:
        return _detail("At least one recognized organization role is required.")
    try:
        keycloak_id = _keycloak_user_id(user)
        _replace_keycloak_roles(keycloak_id, roles)
    except KeycloakAdminError as exc:
        return _detail(str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
    membership = OrganizationMembership.objects.get(user=user, organization_id=organization_id)
    membership.set_roles(roles, oidc_managed=True)
    if not user.oidc_subject:
        user.oidc_subject = keycloak_id
        user.save(update_fields=["oidc_subject"])
    return Response({"id": user.id, "roles": membership.role_codes})


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_user_deletion_impact(request, user_id: str):
    organization_id = request_organization_id(request)
    user = User.objects.filter(id=user_id, organization_memberships__organization_id=organization_id).distinct().first()
    if user is None:
        return _detail("User not found.", status.HTTP_404_NOT_FOUND)
    impact = _deletion_impact(user)
    return Response({"userId": user.id, "blocking": _has_blockers(impact), "impact": impact})


@extend_schema(exclude=True)
@api_view(["DELETE"])
@permission_classes([IsAdmin])
def admin_user_delete(request, user_id: str):
    organization_id = request_organization_id(request)
    user = User.objects.filter(id=user_id, organization_memberships__organization_id=organization_id).distinct().first()
    if user is None:
        return _detail("User not found.", status.HTTP_404_NOT_FOUND)
    if user.id == request.user.id:
        return _detail("You cannot delete your own active administrator account.", status.HTTP_409_CONFLICT)
    impact = _deletion_impact(user)
    if _has_blockers(impact):
        return Response(
            {"detail": "User has blocking business relations.", "impact": impact},
            status=status.HTTP_409_CONFLICT,
        )
    try:
        keycloak_id = _keycloak_user_id(user)
        _kc_request("DELETE", f"/users/{keycloak_id}")
    except KeycloakAdminError as exc:
        return _detail(str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
