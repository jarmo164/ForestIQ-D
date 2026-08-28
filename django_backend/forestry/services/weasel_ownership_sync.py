"""Import Weasel ownership-change pages into the tenant-scoped event projection."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from forestry.models import Cadastre, Owner
from operations.models import OwnershipTransitionEvent

from .weasel_client import WeaselOwnershipClient


def _value(event: dict[str, Any], *names: str) -> str:
    for name in names:
        value = event.get(name)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _occurred_at(event: dict[str, Any]):
    raw = _value(event, "occurredAt", "occurred_at", "timestamp", "date")
    if not raw:
        return None
    parsed = parse_datetime(raw)
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
    return timezone.make_aware(parsed, timezone.get_current_timezone()) if timezone.is_naive(parsed) else parsed


def import_weasel_ownership_deltas(
    *,
    organization_id: str,
    client: WeaselOwnershipClient | None = None,
    cursor: str | None = None,
) -> dict[str, object]:
    """Fetch one bounded delta page and persist its events within one tenant only."""

    page = (client or WeaselOwnershipClient()).ownership_change_page(cursor)
    imported = 0
    duplicates = 0
    ignored = 0
    with transaction.atomic():
        for event in page.events:
            source_id = _value(event, "id", "eventId", "event_id", "reference")
            owner_id = _value(event, "ownerId", "owner_id", "ownerCode", "owner_code")
            cadastre_id = _value(event, "cadastreId", "cadastre_id", "cadastralCode", "cadastral_code")
            owner = Owner.objects.filter(organization_id=organization_id, id=owner_id).first() if owner_id else None
            cadastre = Cadastre.objects.filter(organization_id=organization_id, id=cadastre_id).first() if cadastre_id else None
            if not source_id or (owner is None and cadastre is None):
                ignored += 1
                continue
            record, created = OwnershipTransitionEvent.objects.get_or_create(
                organization_id=organization_id,
                source_reference=f"WEASEL:{source_id}",
                defaults={
                    "owner": owner,
                    "cadastre": cadastre,
                    "event_type": _value(event, "eventType", "event_type", "type") or "OWNERSHIP_CHANGE",
                    "occurred_at": _occurred_at(event),
                    "payload": event,
                },
            )
            if created:
                imported += 1
            else:
                duplicates += 1
    return {"events": imported, "duplicates": duplicates, "ignored": ignored, "nextCursor": page.next_cursor}
