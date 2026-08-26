"""Keycloak Authorization Code + PKCE helpers for ForestIQ's internal JWT boundary."""
from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any
import jwt
import requests
from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction

from accounts.models import Organization, OrganizationMembership, OrganizationRole, User, normalize_organization_roles


class OIDCAuthenticationError(ValueError):
    """Raised when an external OIDC response cannot establish a trusted identity."""


@lru_cache(maxsize=1)
def discovery_document() -> dict[str, Any]:
    """Load the provider metadata once per process; deployment changes require restart."""
    if not settings.KEYCLOAK_OIDC_ENABLED:
        raise OIDCAuthenticationError("Keycloak OIDC is not enabled.")
    try:
        response = requests.get(settings.KEYCLOAK_DISCOVERY_URL, timeout=settings.KEYCLOAK_HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        document = response.json()
    except (requests.RequestException, ValueError) as error:
        raise OIDCAuthenticationError("Keycloak metadata could not be retrieved.") from error
    required = {"authorization_endpoint", "token_endpoint", "jwks_uri", "issuer"}
    if not required.issubset(document):
        raise OIDCAuthenticationError("Keycloak metadata is incomplete.")
    return document


def public_configuration() -> dict[str, Any]:
    """Return only browser-safe OIDC settings; secrets are never exposed."""
    if not settings.KEYCLOAK_OIDC_ENABLED:
        return {"enabled": False, "localLoginEnabled": settings.FORESTIQ_DEVMODE}
    document = discovery_document()
    return {
        "enabled": True,
        "localLoginEnabled": settings.FORESTIQ_DEVMODE,
        "authorizationEndpoint": document["authorization_endpoint"],
        "clientId": settings.KEYCLOAK_CLIENT_ID,
        "scope": settings.KEYCLOAK_SCOPES,
    }


def _claim_value(claims: dict[str, Any], path: str) -> Any:
    value: Any = claims
    for segment in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(segment)
    return value


def _claim_roles(claims: dict[str, Any]) -> list[str]:
    realm_roles = _claim_value(claims, "realm_access.roles") or []
    resource_roles = _claim_value(claims, f"resource_access.{settings.KEYCLOAK_CLIENT_ID}.roles") or []
    return normalize_organization_roles([*realm_roles, *resource_roles])


def _claim_organization(claims: dict[str, Any]) -> Organization:
    raw_value = _claim_value(claims, settings.KEYCLOAK_ORGANIZATION_CLAIM)
    if isinstance(raw_value, dict):
        raw_value = raw_value.get("id") or raw_value.get("slug")
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise OIDCAuthenticationError("Keycloak token does not contain an organization claim.")
    identifier = raw_value.strip()
    organization = Organization.objects.filter(is_active=True).filter(
        models.Q(id=identifier) | models.Q(slug=identifier)
    ).first()
    if organization is None:
        raise OIDCAuthenticationError("Keycloak organization is not an active ForestIQ organization.")
    return organization


def _jwks_key(token: str, jwks_uri: str):
    """Resolve and cache the selected JWK without trusting token claims first."""
    try:
        header = jwt.get_unverified_header(token)
        key_id = header["kid"]
    except (jwt.PyJWTError, KeyError) as error:
        raise OIDCAuthenticationError("Keycloak ID token has no usable signing key.") from error

    cache_key = f"forestiq:keycloak:jwk:{key_id}"
    cached = cache.get(cache_key)
    if cached:
        return jwt.PyJWK.from_dict(cached).key
    try:
        response = requests.get(jwks_uri, timeout=settings.KEYCLOAK_HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        keys = response.json().get("keys", [])
        selected = next(key for key in keys if key.get("kid") == key_id)
    except (requests.RequestException, ValueError, StopIteration) as error:
        raise OIDCAuthenticationError("Keycloak signing key could not be resolved.") from error
    cache.set(cache_key, selected, settings.KEYCLOAK_JWKS_CACHE_SECONDS)
    return jwt.PyJWK.from_dict(selected).key


def _verified_claims(id_token: str, document: dict[str, Any], nonce: str | None = None) -> dict[str, Any]:
    key = _jwks_key(id_token, document["jwks_uri"])
    try:
        claims = jwt.decode(
            id_token,
            key=key,
            algorithms=["RS256", "RS384", "RS512", "PS256", "PS384", "PS512", "ES256", "ES384", "ES512"],
            audience=settings.KEYCLOAK_CLIENT_ID,
            issuer=document["issuer"],
            leeway=settings.KEYCLOAK_CLOCK_SKEW_SECONDS,
        )
    except jwt.PyJWTError as error:
        raise OIDCAuthenticationError("Keycloak ID token validation failed.") from error
    if nonce and claims.get("nonce") != nonce:
        raise OIDCAuthenticationError("Keycloak ID token nonce does not match the login request.")
    return claims


def exchange_authorization_code(*, code: str, code_verifier: str, redirect_uri: str, nonce: str | None = None) -> tuple[User, OrganizationMembership]:
    """Exchange a PKCE code, validate its ID token and sync a tenant membership."""
    if not code or not code_verifier or not redirect_uri:
        raise OIDCAuthenticationError("Authorization code, verifier and redirect URI are required.")
    document = discovery_document()
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.KEYCLOAK_CLIENT_ID,
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    try:
        response = requests.post(document["token_endpoint"], data=payload, timeout=settings.KEYCLOAK_HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        tokens = response.json()
    except (requests.RequestException, ValueError) as error:
        raise OIDCAuthenticationError("Keycloak authorization code exchange failed.") from error
    id_token = tokens.get("id_token")
    if not isinstance(id_token, str):
        raise OIDCAuthenticationError("Keycloak response did not contain an ID token.")

    claims = _verified_claims(id_token, document, nonce)
    subject = str(claims.get("sub") or "").strip()
    if not subject:
        raise OIDCAuthenticationError("Keycloak ID token does not contain a subject.")
    roles = _claim_roles(claims)
    if not roles:
        raise OIDCAuthenticationError("Keycloak token does not contain a recognized ForestIQ role.")
    organization = _claim_organization(claims)
    display_name = str(claims.get("name") or claims.get("preferred_username") or subject).strip()[:100]

    with transaction.atomic():
        user = User.objects.filter(oidc_subject=subject).first()
        created = False
        if user is None:
            # A legacy user can retain an identical short identifier. Longer
            # Keycloak subjects receive a deterministic non-sensitive ID while
            # oidc_subject remains the immutable external identity key.
            legacy_user = User.objects.filter(id=subject).first() if len(subject) <= 50 else None
            if legacy_user is not None and legacy_user.oidc_subject in (None, ""):
                user = legacy_user
            else:
                user_id = subject if len(subject) <= 50 else f"oidc-{hashlib.sha256(subject.encode()).hexdigest()[:45]}"
                user = User(id=user_id, full_name=display_name, is_active=True, default_organization=organization)
                created = True
        if not user.is_active:
            raise OIDCAuthenticationError("The corresponding ForestIQ user is inactive.")
        changed_fields = []
        if user.oidc_subject != subject:
            user.oidc_subject = subject
            changed_fields.append("oidc_subject")
        if user.full_name != display_name:
            user.full_name = display_name
            changed_fields.append("full_name")
        if created or user.default_organization_id is None:
            user.default_organization = organization
            changed_fields.append("default_organization")
        if created:
            user.save()
        elif changed_fields:
            user.save(update_fields=changed_fields)

        membership, _ = OrganizationMembership.objects.get_or_create(organization=organization, user=user)
        membership.roles = normalize_organization_roles([OrganizationRole.MEMBER, *roles])
        membership.oidc_managed = True
        membership.save(update_fields=["roles", "oidc_managed", "updated_at"])
    return user, membership
