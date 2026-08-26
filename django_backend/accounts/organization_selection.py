"""Safe organization lookup helpers for trusted administration commands."""

from __future__ import annotations

from uuid import UUID

from accounts.models import Organization


def active_organization(identifier: str) -> Organization | None:
    """Find an active organization by UUID or stable slug without invalid UUID queries."""

    try:
        organization_id = UUID(str(identifier))
    except (TypeError, ValueError):
        return Organization.objects.filter(slug=str(identifier), is_active=True).first()
    return Organization.objects.filter(id=organization_id, is_active=True).first()
