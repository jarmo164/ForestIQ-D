"""P3 platform-control APIs: stable notification history, map services, realtime and preferences."""
from __future__ import annotations

import base64
from datetime import date, datetime, timedelta, timezone as dt_timezone
import json

from django.conf import settings
from django.db.models import DateTimeField, F, Q, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from forestry.models import Cadastre, CadastreNotification
from operations.models import ApplicationMessage
from operations.p3_models import NotificationPreference
from operations.realtime import publish_org_event, unread_application_message_count
from operations.notifications import SUPPORTED_CHANNELS, SUPPORTED_EVENTS
from .permissions import CanUseAssignedOwners, CanViewOrganizationData, can_access_owner
from .serializers import notification_data


_NOTIFICATION_PAGE_MAX = 100
_ARCHIVE_RANGE_MAX_DAYS = 366
_CURSOR_FALLBACK = datetime(1970, 1, 1, tzinfo=dt_timezone.utc)


def _detail(message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> Response:
    return Response({"detail": message}, status=http_status)


def _cadastre_or_403(request, cadastre_id: str):
    cadastre = get_object_or_404(Cadastre.objects.prefetch_related("owners"), id=cadastre_id)
    if not any(can_access_owner(request, owner) for owner in cadastre.owners.all()):
        return None, _detail("You do not have access to this cadastre.", status.HTTP_403_FORBIDDEN)
    return cadastre, None


def _page_size(request) -> int:
    try:
        value = int(request.query_params.get("limit", 50))
    except (TypeError, ValueError) as exc:
        raise ValueError("limit must be an integer.") from exc
    if value < 1 or value > _NOTIFICATION_PAGE_MAX:
        raise ValueError(f"limit must be between 1 and {_NOTIFICATION_PAGE_MAX}.")
    return value


def _encode_notification_cursor(sort_date: datetime, notification_id: int) -> str:
    raw = json.dumps({"at": sort_date.isoformat(), "id": notification_id}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_notification_cursor(value: str | None) -> tuple[datetime, int] | None:
    if not value:
        return None
    try:
        padded = value + "=" * (-len(value) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
        anchor = datetime.fromisoformat(str(payload["at"]).replace("Z", "+00:00"))
        if anchor.tzinfo is None:
            anchor = anchor.replace(tzinfo=dt_timezone.utc)
        return anchor, int(payload["id"])
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("cursor is invalid.") from exc


def _notification_page(request, *, cadastre: Cadastre, archived: bool, from_date: date | None = None, to_date: date | None = None):
    try:
        limit = _page_size(request)
        cursor = _decode_notification_cursor(request.query_params.get("cursor"))
    except ValueError as exc:
        return _detail(str(exc))

    sort_expression = (
        Coalesce("archive_date", "registration_date", Value(_CURSOR_FALLBACK, output_field=DateTimeField()))
        if archived
        else Coalesce("registration_date", Value(_CURSOR_FALLBACK, output_field=DateTimeField()))
    )
    queryset = CadastreNotification.objects.filter(cadastre=cadastre, archived=archived).annotate(_sort_date=sort_expression)
    if from_date is not None and to_date is not None:
        start = datetime.combine(from_date, datetime.min.time(), tzinfo=dt_timezone.utc)
        end = datetime.combine(to_date + timedelta(days=1), datetime.min.time(), tzinfo=dt_timezone.utc)
        queryset = queryset.filter(_sort_date__gte=start, _sort_date__lt=end)
    if cursor:
        anchor, notification_id = cursor
        queryset = queryset.filter(Q(_sort_date__lt=anchor) | Q(_sort_date=anchor, id__lt=notification_id))
    rows = list(queryset.order_by(F("_sort_date").desc(), "-id")[: limit + 1])
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = None
    if has_more and rows:
        next_cursor = _encode_notification_cursor(rows[-1]._sort_date, rows[-1].id)
    return Response({"items": [notification_data(item) for item in rows], "nextCursor": next_cursor, "pageSize": limit})


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def cadastre_active_notifications(request, cadastre_id: str):
    """Return current notices with a stable two-part keyset cursor."""
    cadastre, denied = _cadastre_or_403(request, cadastre_id)
    if denied:
        return denied
    return _notification_page(request, cadastre=cadastre, archived=False)


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def cadastre_archived_notifications(request, cadastre_id: str):
    """Return archive notices only inside an explicit bounded date range."""
    cadastre, denied = _cadastre_or_403(request, cadastre_id)
    if denied:
        return denied
    from_value = parse_date(str(request.query_params.get("from", "")))
    to_value = parse_date(str(request.query_params.get("to", "")))
    if from_value is None or to_value is None:
        return _detail("from and to are required ISO dates for archive queries.")
    if to_value < from_value:
        return _detail("to must not be earlier than from.")
    if (to_value - from_value).days > _ARCHIVE_RANGE_MAX_DAYS:
        return _detail(f"Archive range must not exceed {_ARCHIVE_RANGE_MAX_DAYS} days.")
    return _notification_page(request, cadastre=cadastre, archived=True, from_date=from_value, to_date=to_value)


@api_view(["GET", "PUT"])
@permission_classes([CanViewOrganizationData])
def notification_preferences(request):
    """Read or replace only the authenticated user's delivery policy."""
    preference = NotificationPreference.objects.filter(user=request.user).first()
    if request.method == "GET":
        return Response({
            "enabled": preference.enabled if preference else True,
            "eventTypes": preference.event_types if preference else ["REMINDER_DUE"],
            "channels": preference.channels if preference else ["IN_APP"],
            "supportedEventTypes": sorted(SUPPORTED_EVENTS),
            "supportedChannels": sorted(SUPPORTED_CHANNELS),
        })

    event_types = request.data.get("eventTypes", ["REMINDER_DUE"])
    channels = request.data.get("channels", ["IN_APP"])
    if not isinstance(event_types, list) or any(item not in SUPPORTED_EVENTS for item in event_types):
        return _detail("eventTypes contains an unsupported notification event.")
    if not isinstance(channels, list) or any(item not in SUPPORTED_CHANNELS for item in channels):
        return _detail("channels contains an unsupported notification channel.")
    enabled = request.data.get("enabled", True)
    if not isinstance(enabled, bool):
        return _detail("enabled must be a boolean.")
    preference, _ = NotificationPreference.objects.update_or_create(
        user=request.user,
        defaults={"enabled": enabled, "event_types": event_types, "channels": channels},
    )
    return Response({
        "enabled": preference.enabled,
        "eventTypes": preference.event_types,
        "channels": preference.channels,
        "supportedEventTypes": sorted(SUPPORTED_EVENTS),
        "supportedChannels": sorted(SUPPORTED_CHANNELS),
    })


def _application_message_data(message: ApplicationMessage) -> dict:
    return {
        "id": message.pk,
        "text": message.text,
        "category": message.category or None,
        "eventKey": message.event_key or None,
        "createdAt": int(message.created_at.timestamp() * 1000),
        "readAt": int(message.read_at.timestamp() * 1000) if message.read_at else None,
        "archivedAt": int(message.archived_at.timestamp() * 1000) if message.archived_at else None,
    }


def _publish_unread_count(request):
    publish_org_event(
        "APPLICATION_MESSAGE_COUNT",
        {"unreadCount": unread_application_message_count(request.user)},
        actor=request.user,
        recipient=request.user,
        topic="user",
    )


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def application_messages(request):
    records = ApplicationMessage.objects.filter(recipient=request.user)
    include_archived = str(request.query_params.get("includeArchived", "false")).lower() == "true"
    if not include_archived:
        records = records.filter(archived_at__isnull=True)
    try:
        limit = min(max(int(request.query_params.get("limit", 100)), 1), 200)
    except (TypeError, ValueError):
        return _detail("limit must be an integer.")
    rows = list(records.order_by("-created_at", "-id")[:limit])
    return Response({
        "items": [_application_message_data(item) for item in rows],
        "unreadCount": unread_application_message_count(request.user),
    })


@api_view(["PATCH", "DELETE"])
@permission_classes([CanViewOrganizationData])
def application_message_detail(request, message_id: int):
    message = get_object_or_404(ApplicationMessage, pk=message_id, recipient=request.user)
    if request.method == "DELETE":
        if message.archived_at is None:
            return _detail("Archive the message before deleting it.", status.HTTP_409_CONFLICT)
        delete_after = message.archived_at + timedelta(days=settings.FORESTIQ_APPLICATION_MESSAGE_DELETE_AFTER_DAYS)
        if timezone.now() < delete_after:
            return _detail(
                f"Archived messages are retained for {settings.FORESTIQ_APPLICATION_MESSAGE_DELETE_AFTER_DAYS} days.",
                status.HTTP_409_CONFLICT,
            )
        message.delete()
        _publish_unread_count(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    operation = str(request.data.get("operation", "")).upper()
    now = timezone.now()
    if operation == "READ":
        if message.read_at is None:
            message.read_at = now
            message.save(update_fields=("read_at",))
    elif operation == "ARCHIVE":
        message.read_at = message.read_at or now
        message.archived_at = now
        message.save(update_fields=("read_at", "archived_at"))
    else:
        return _detail("operation must be READ or ARCHIVE.")
    _publish_unread_count(request)
    return Response(_application_message_data(message))


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def application_message_unread_count(request):
    return Response({"unreadCount": unread_application_message_count(request.user)})
