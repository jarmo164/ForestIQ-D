"""Organization-bound company profiles and immutable contract template versions."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email, validate_slug
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import Organization
from operations.models import CompanyProfile, ContractTemplate

from .concurrency import missing_version_response, requested_version, version_conflict_response
from .organization import request_organization_id
from .permissions import IsAdmin


MAX_TEMPLATE_HTML_BYTES = 512_000


def _detail(message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> Response:
    return Response({"detail": message}, status=http_status)


def _organization(request) -> Organization:
    return get_object_or_404(Organization, id=request_organization_id(request))


def _company_data(profile: CompanyProfile) -> dict:
    return {
        "id": str(profile.id),
        "legalName": profile.legal_name,
        "registryCode": profile.registry_code or None,
        "vatNumber": profile.vat_number or None,
        "address": profile.address or None,
        "email": profile.email or None,
        "phone": profile.phone or None,
        "iban": profile.iban or None,
        "signatoryName": profile.signatory_name or None,
        "website": profile.website or None,
        "version": profile.version,
        "createdAt": profile.created_at,
        "updatedAt": profile.updated_at,
    }


def _template_data(template: ContractTemplate) -> dict:
    return {
        "id": str(template.id),
        "companyProfileId": str(template.company_profile_id) if template.company_profile_id else None,
        "templateKey": template.template_key,
        "name": template.name,
        "description": template.description or None,
        "html": template.html,
        "version": template.version,
        "isActive": template.is_active,
        "supersedesId": str(template.supersedes_id) if template.supersedes_id else None,
        "createdAt": template.created_at,
    }


def template_snapshot(template: ContractTemplate) -> dict:
    """Return immutable data copied onto a contract at generation time."""

    return {
        "templateId": str(template.id),
        "templateKey": template.template_key,
        "version": template.version,
        "name": template.name,
        "html": template.html,
        "companyProfile": _company_data(template.company_profile) if template.company_profile else None,
    }


def _text(data, name: str, *, required: bool = False, maximum: int = 0) -> str:
    value = str(data.get(name, "")).strip()
    if required and not value:
        raise ValueError(f"{name} is required.")
    if maximum and len(value) > maximum:
        raise ValueError(f"{name} may contain at most {maximum} characters.")
    return value


def _profile_values(data) -> dict:
    legal_name = _text(data, "legalName", required=True, maximum=255)
    email = _text(data, "email", maximum=254)
    website = _text(data, "website", maximum=500)
    try:
        if email:
            validate_email(email)
        if website:
            URLValidator(schemes=["http", "https"])(website)
    except ValidationError as exc:
        raise ValueError(exc.messages[0]) from exc
    return {
        "legal_name": legal_name,
        "registry_code": _text(data, "registryCode", maximum=64),
        "vat_number": _text(data, "vatNumber", maximum=64),
        "address": _text(data, "address", maximum=5000),
        "email": email,
        "phone": _text(data, "phone", maximum=64),
        "iban": _text(data, "iban", maximum=64),
        "signatory_name": _text(data, "signatoryName", maximum=255),
        "website": website,
    }


def _template_values(data, organization: Organization, *, fallback: ContractTemplate | None = None) -> dict:
    template_key = _text(data, "templateKey", required=fallback is None, maximum=80) or (fallback.template_key if fallback else "")
    name = _text(data, "name", required=fallback is None, maximum=255) or (fallback.name if fallback else "")
    html = str(data.get("html", fallback.html if fallback else ""))
    description = _text(data, "description", maximum=5000) if "description" in data else (fallback.description if fallback else "")
    if not html.strip():
        raise ValueError("html is required.")
    if len(html.encode("utf-8")) > MAX_TEMPLATE_HTML_BYTES:
        raise ValueError(f"html exceeds the {MAX_TEMPLATE_HTML_BYTES} byte safety limit.")
    try:
        validate_slug(template_key)
    except ValidationError as exc:
        raise ValueError("templateKey must be a lowercase slug using letters, numbers, hyphens or underscores.") from exc
    profile_id = data.get("companyProfileId", fallback.company_profile_id if fallback else None)
    if profile_id in {"", None}:
        company_profile = None
    else:
        company_profile = get_object_or_404(CompanyProfile.objects.filter(organization=organization), id=profile_id)
    return {
        "template_key": template_key,
        "name": name,
        "description": description,
        "html": html,
        "company_profile": company_profile,
    }


def _template_queryset(request):
    return ContractTemplate.objects.select_related("company_profile", "supersedes").filter(organization=_organization(request))


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def company_profiles(request):
    organization = _organization(request)
    if request.method == "GET":
        return Response([_company_data(item) for item in CompanyProfile.objects.filter(organization=organization)])
    try:
        values = _profile_values(request.data)
    except ValueError as exc:
        return _detail(str(exc))
    try:
        profile = CompanyProfile.objects.create(organization=organization, **values)
    except IntegrityError:
        return _detail("registryCode must be unique within the organization.", status.HTTP_409_CONFLICT)
    return Response(_company_data(profile), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAdmin])
def company_profile_detail(request, profile_id: str):
    profile = get_object_or_404(CompanyProfile.objects.filter(organization=_organization(request)), id=profile_id)
    if request.method == "GET":
        return Response(_company_data(profile))
    if request.method == "DELETE":
        if profile.contract_templates.filter(is_active=True).exists():
            return _detail("Archive or reassign active contract templates before deleting this company profile.", status.HTTP_409_CONFLICT)
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    expected_version = requested_version(request)
    if expected_version is None:
        return missing_version_response()
    try:
        values = _profile_values({**_company_data(profile), **request.data})
    except ValueError as exc:
        return _detail(str(exc))
    if profile.version != expected_version:
        return version_conflict_response(profile, expected_version)
    try:
        updated = CompanyProfile.objects.filter(id=profile.id, version=expected_version).update(**values, version=expected_version + 1)
    except IntegrityError:
        return _detail("registryCode must be unique within the organization.", status.HTTP_409_CONFLICT)
    if not updated:
        profile.refresh_from_db(fields=["version"])
        return version_conflict_response(profile, expected_version)
    profile.refresh_from_db()
    return Response(_company_data(profile))


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def contract_templates(request):
    templates = _template_queryset(request)
    if request.method == "GET":
        active_only = request.query_params.get("active") == "true"
        if active_only:
            templates = templates.filter(is_active=True)
        return Response([_template_data(item) for item in templates])
    organization = _organization(request)
    try:
        values = _template_values(request.data, organization)
    except ValueError as exc:
        return _detail(str(exc))
    with transaction.atomic():
        active = (
            ContractTemplate.objects.select_for_update()
            .filter(organization=organization, template_key=values["template_key"], is_active=True)
            .first()
        )
        if active:
            return _detail("An active version of this templateKey already exists; PATCH it to create the next version.", status.HTTP_409_CONFLICT)
        next_version = (templates.filter(template_key=values["template_key"]).aggregate(highest=Max("version"))["highest"] or 0) + 1
        template = ContractTemplate.objects.create(organization=organization, version=next_version, created_by=request.user, **values)
    return Response(_template_data(template), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAdmin])
def contract_template_detail(request, template_id: str):
    template = get_object_or_404(_template_queryset(request), id=template_id)
    if request.method == "GET":
        return Response(_template_data(template))
    expected_version = requested_version(request)
    if expected_version is None:
        return missing_version_response()
    if template.version != expected_version:
        return version_conflict_response(template, expected_version)
    if request.method == "DELETE":
        if not template.is_active:
            return Response(_template_data(template))
        template.is_active = False
        template.save(update_fields=["is_active"])
        return Response(_template_data(template))
    if not template.is_active:
        return _detail("Only the active template version can be revised.", status.HTTP_409_CONFLICT)
    organization = _organization(request)
    try:
        values = _template_values(request.data, organization, fallback=template)
    except ValueError as exc:
        return _detail(str(exc))
    with transaction.atomic():
        current = ContractTemplate.objects.select_for_update().get(id=template.id)
        if not current.is_active or current.version != expected_version:
            return version_conflict_response(current, expected_version)
        current.is_active = False
        current.save(update_fields=["is_active"])
        successor = ContractTemplate.objects.create(
            organization=organization,
            version=current.version + 1,
            supersedes=current,
            created_by=request.user,
            **values,
        )
    return Response(_template_data(successor), status=status.HTTP_201_CREATED)
