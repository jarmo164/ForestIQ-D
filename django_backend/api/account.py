"""Authenticated account overview for the ForestIQ user workspace."""

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import OrganizationMembership
from api.organization import request_organization_id


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def account_profile(request):
    organization_id = request_organization_id(request)
    membership = getattr(request, "organization_membership", None)
    if membership is None or str(membership.organization_id) != str(organization_id):
        membership = OrganizationMembership.objects.select_related("organization").get(
            user=request.user,
            organization_id=organization_id,
        )
    else:
        membership = OrganizationMembership.objects.select_related("organization").get(pk=membership.pk)

    return Response(
        {
            "user": {"id": request.user.id, "name": request.user.full_name},
            "organization": {
                "id": str(membership.organization_id),
                "slug": membership.organization.slug,
                "name": membership.organization.name,
            },
            "roles": membership.role_codes,
            "privileges": membership.privilege_codes,
            "security": {
                "sessionType": "JWT",
                "passwordChangeAvailable": bool(settings.FORESTIQ_DEVMODE),
            },
        }
    )
