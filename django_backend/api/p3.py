"""P3 platform-control APIs: stable notification history, map services, realtime and preferences."""
from __future__ import annotations

import base64
from datetime import date, datetime, timedelta, timezone as dt_timezone
import json
import ipaddress
import time
from urllib.parse import urlparse

import requests

from django.conf import settings
from django.db.models import DateTimeField, F, Q, Value
from django.core.cache import cache
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from forestry.models import Cadastre, CadastreNotification
from forestry.p3_models import BasemapDefinition, ExternalMapLayer, WfsGeneration, WfsLayerManifest
from operations.models import ApplicationMessage
from operations.p3_models import NotificationPreference
from operations.realtime import publish_org_event, unread_application_message_count
from operations.notifications import SUPPORTED_CHANNELS, SUPPORTED_EVENTS
from forestry.services.external_sync import ExternalSourceError
from forestry.services.wfs_generations import (
    approve_schema_drift,
    cleanup_retired_generations,
    deep_verify,
    ensure_default_manifests,
    publish_generation,
    rollback_generation,
)
from .organization import request_organization_id
from .permissions import CanUseAssignedOwners, CanViewOrganizationData, IsAdmin, can_access_owner
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


_MAP_TILE_MAX_BYTES = 3 * 1024 * 1024


def _basemap_data(item: BasemapDefinition | None = None) -> dict:
    if item is None:
        return {
            "key": "default",
            "name": "OpenFreeMap",
            "attribution": "© OpenFreeMap",
            "enabled": True,
            "maxZoom": 19,
            "cacheSeconds": settings.FORESTIQ_MAP_BASEMAP_CACHE_SECONDS,
            "tileTemplate": "/api/services/map/basemaps/default/{z}/{x}/{y}",
        }
    return {
        "key": item.key,
        "name": item.name,
        "attribution": item.attribution,
        "enabled": item.enabled,
        "maxZoom": item.max_zoom,
        "cacheSeconds": item.cache_seconds,
        "tileTemplate": f"/api/services/map/basemaps/{item.key}/{{z}}/{{x}}/{{y}}",
    }


def _external_layer_data(item: ExternalMapLayer) -> dict:
    return {
        "id": str(item.id),
        "key": item.key,
        "name": item.name,
        "serviceType": item.service_type,
        "sourceLayer": item.source_layer or None,
        "visible": item.visible,
        "opacity": float(item.opacity),
        "usageRights": item.usage_rights or None,
        "attribution": item.attribution or None,
        "freshnessAt": int(item.freshness_at.timestamp() * 1000) if item.freshness_at else None,
        "minZoom": item.min_zoom,
        "maxZoom": item.max_zoom,
        "tileTemplate": f"/api/services/map/external-layers/{item.key}/{{z}}/{{x}}/{{y}}",
        "updatedAt": int(item.updated_at.timestamp() * 1000),
    }


def _validate_external_template(value: str) -> str:
    value = str(value or "").strip()
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("External map URL must use https.")
    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise ValueError("Local network map targets are not allowed.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address and (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved):
        raise ValueError("Private or reserved map targets are not allowed.")
    if not any(token in value for token in ("{z}", "{bbox}")):
        raise ValueError("Map URL template must contain {z} or {bbox}.")
    return value


def _tile_bbox_3857(z: int, x: int, y: int) -> str:
    origin = 20037508.342789244
    tiles = 2 ** z
    size = (origin * 2) / tiles
    min_x = -origin + x * size
    max_x = min_x + size
    max_y = origin - y * size
    min_y = max_y - size
    return f"{min_x:.3f},{min_y:.3f},{max_x:.3f},{max_y:.3f}"


def _render_tile_url(template: str, z: int, x: int, y: int) -> str:
    return (
        template.replace("{z}", str(z))
        .replace("{x}", str(x))
        .replace("{y}", str(y))
        .replace("{bbox}", _tile_bbox_3857(z, x, y))
    )


def _proxy_tile(url: str, *, cache_key: str, cache_seconds: int):
    cached = cache.get(cache_key)
    if cached is not None:
        body, content_type = cached
        response = HttpResponse(body, content_type=content_type)
        response["Cache-Control"] = f"private, max-age={cache_seconds}"
        response["X-ForestIQ-Map-Cache"] = "HIT"
        return response
    last_error = None
    for attempt in range(settings.FORESTIQ_MAP_PROXY_RETRIES + 1):
        try:
            response = requests.get(
                url,
                timeout=settings.FORESTIQ_MAP_PROXY_TIMEOUT_SECONDS,
                headers={"User-Agent": settings.FORESTIQ_SYNC_USER_AGENT, "Accept": "image/*,application/x-protobuf,application/vnd.mapbox-vector-tile,*/*"},
            )
            response.raise_for_status()
            if len(response.content) > _MAP_TILE_MAX_BYTES:
                return _detail("Upstream map tile exceeded the response-size policy.", status.HTTP_502_BAD_GATEWAY)
            content_type = response.headers.get("Content-Type", "application/octet-stream").split(";", 1)[0]
            cache.set(cache_key, (response.content, content_type), timeout=cache_seconds)
            proxied = HttpResponse(response.content, content_type=content_type)
            proxied["Cache-Control"] = f"private, max-age={cache_seconds}"
            proxied["X-ForestIQ-Map-Cache"] = "MISS"
            return proxied
        except requests.RequestException as exc:
            last_error = exc
            if attempt < settings.FORESTIQ_MAP_PROXY_RETRIES:
                time.sleep(min(0.15 * (2 ** attempt), 0.6))
    return _detail(f"Upstream map service is unavailable: {last_error}", status.HTTP_502_BAD_GATEWAY)


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def map_configuration(request):
    basemaps = list(BasemapDefinition.objects.filter(enabled=True))
    return Response({
        "basemaps": [_basemap_data(item) for item in basemaps] or [_basemap_data()],
        "externalLayers": [_external_layer_data(item) for item in ExternalMapLayer.objects.all()],
    })


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def basemap_tile(request, key: str, z: int, x: int, y: int):
    if z < 0 or z > 22 or x < 0 or y < 0 or x >= 2 ** z or y >= 2 ** z:
        return _detail("Invalid tile coordinates.")
    item = BasemapDefinition.objects.filter(key=key, enabled=True).first()
    if item:
        template, ttl = item.tile_url_template, item.cache_seconds
    elif key == "default":
        template, ttl = settings.FORESTIQ_DEFAULT_BASEMAP_TILE_URL, settings.FORESTIQ_MAP_BASEMAP_CACHE_SECONDS
    else:
        return _detail("Unknown basemap.", status.HTTP_404_NOT_FOUND)
    url = _render_tile_url(template, z, x, y)
    return _proxy_tile(url, cache_key=f"p3:basemap:{request_organization_id(request)}:{key}:{z}:{x}:{y}", cache_seconds=ttl)


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def external_layer_tile(request, key: str, z: int, x: int, y: int):
    if z < 0 or z > 22 or x < 0 or y < 0 or x >= 2 ** z or y >= 2 ** z:
        return _detail("Invalid tile coordinates.")
    layer = get_object_or_404(ExternalMapLayer, key=key)
    if z < layer.min_zoom or z > layer.max_zoom:
        return Response(status=status.HTTP_204_NO_CONTENT)
    url = _render_tile_url(layer.url_template, z, x, y)
    return _proxy_tile(
        url,
        cache_key=f"p3:external:{request_organization_id(request)}:{key}:{z}:{x}:{y}",
        cache_seconds=layer.cache_seconds,
    )


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def admin_basemaps(request):
    if request.method == "GET":
        return Response([_basemap_data(item) for item in BasemapDefinition.objects.all()])
    try:
        template = _validate_external_template(request.data.get("tileUrlTemplate"))
    except ValueError as exc:
        return _detail(str(exc))
    key = str(request.data.get("key", "")).strip().lower()
    name = str(request.data.get("name", "")).strip()
    if not key or not name:
        return _detail("key and name are required.")
    item = BasemapDefinition.objects.create(
        key=key,
        name=name,
        tile_url_template=template,
        attribution=str(request.data.get("attribution", "")),
        enabled=bool(request.data.get("enabled", True)),
        max_zoom=min(max(int(request.data.get("maxZoom", 19)), 0), 22),
        cache_seconds=min(max(int(request.data.get("cacheSeconds", 3600)), 30), 86400),
    )
    return Response(_basemap_data(item), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAdmin])
def admin_basemap_detail(request, key: str):
    item = get_object_or_404(BasemapDefinition, key=key)
    if request.method == "DELETE":
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if "tileUrlTemplate" in request.data:
        try:
            item.tile_url_template = _validate_external_template(request.data.get("tileUrlTemplate"))
        except ValueError as exc:
            return _detail(str(exc))
    for field, api_key in (("name", "name"), ("attribution", "attribution")):
        if api_key in request.data:
            setattr(item, field, str(request.data.get(api_key, "")).strip())
    if "enabled" in request.data:
        if not isinstance(request.data["enabled"], bool):
            return _detail("enabled must be a boolean.")
        item.enabled = request.data["enabled"]
    item.save()
    return Response(_basemap_data(item))


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def admin_external_layers(request):
    if request.method == "GET":
        return Response([_external_layer_data(item) for item in ExternalMapLayer.objects.all()])
    try:
        template = _validate_external_template(request.data.get("urlTemplate"))
        opacity = float(request.data.get("opacity", 0.75))
    except (ValueError, TypeError) as exc:
        return _detail(str(exc))
    service_type = str(request.data.get("serviceType", "")).upper()
    if service_type not in ExternalMapLayer.ServiceType.values:
        return _detail("serviceType must be WMS or MVT.")
    if opacity < 0 or opacity > 1:
        return _detail("opacity must be between 0 and 1.")
    key = str(request.data.get("key", "")).strip().lower()
    name = str(request.data.get("name", "")).strip()
    if not key or not name:
        return _detail("key and name are required.")
    item = ExternalMapLayer.objects.create(
        key=key,
        name=name,
        service_type=service_type,
        url_template=template,
        source_layer=str(request.data.get("sourceLayer", "")).strip(),
        visible=bool(request.data.get("visible", False)),
        opacity=opacity,
        usage_rights=str(request.data.get("usageRights", "")).strip(),
        attribution=str(request.data.get("attribution", "")).strip(),
        min_zoom=min(max(int(request.data.get("minZoom", 0)), 0), 22),
        max_zoom=min(max(int(request.data.get("maxZoom", 22)), 0), 22),
        cache_seconds=min(max(int(request.data.get("cacheSeconds", 300)), 30), 86400),
    )
    return Response(_external_layer_data(item), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAdmin])
def admin_external_layer_detail(request, key: str):
    item = get_object_or_404(ExternalMapLayer, key=key)
    if request.method == "DELETE":
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if "urlTemplate" in request.data:
        try:
            item.url_template = _validate_external_template(request.data.get("urlTemplate"))
        except ValueError as exc:
            return _detail(str(exc))
    if "serviceType" in request.data:
        value = str(request.data.get("serviceType", "")).upper()
        if value not in ExternalMapLayer.ServiceType.values:
            return _detail("serviceType must be WMS or MVT.")
        item.service_type = value
    scalar_fields = {
        "name": "name", "sourceLayer": "source_layer", "usageRights": "usage_rights", "attribution": "attribution",
    }
    for api_key, field in scalar_fields.items():
        if api_key in request.data:
            setattr(item, field, str(request.data.get(api_key, "")).strip())
    if "visible" in request.data:
        if not isinstance(request.data["visible"], bool):
            return _detail("visible must be a boolean.")
        item.visible = request.data["visible"]
    if "opacity" in request.data:
        try:
            opacity = float(request.data["opacity"])
        except (TypeError, ValueError):
            return _detail("opacity must be numeric.")
        if opacity < 0 or opacity > 1:
            return _detail("opacity must be between 0 and 1.")
        item.opacity = opacity
    if "freshnessAt" in request.data:
        from django.utils.dateparse import parse_datetime
        parsed = parse_datetime(str(request.data["freshnessAt"]).replace("Z", "+00:00"))
        if parsed is None:
            return _detail("freshnessAt must be an ISO datetime.")
        item.freshness_at = parsed
    item.save()
    return Response(_external_layer_data(item))


def _map_search_result(cadastre: Cadastre) -> dict:
    return {
        "id": cadastre.id,
        "label": cadastre.name or cadastre.address or cadastre.id,
        "cadastreId": cadastre.id,
        "address": cadastre.address or None,
        "source": "LOCAL",
    }


def _inaks_rate_allowed(request) -> bool:
    minute = int(time.time() // 60)
    key = f"p3:inaks-rate:{request_organization_id(request)}:{request.user.id}:{minute}"
    if cache.add(key, 1, timeout=70):
        return True
    try:
        return cache.incr(key) <= settings.FORESTIQ_INAKS_RATE_PER_MINUTE
    except ValueError:
        cache.set(key, 1, timeout=70)
        return True


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def map_search(request):
    query = str(request.query_params.get("q", "")).strip()
    if len(query) < 2 or len(query) > settings.FORESTIQ_MAP_SEARCH_MAX_QUERY_LENGTH:
        return _detail(f"q must contain 2-{settings.FORESTIQ_MAP_SEARCH_MAX_QUERY_LENGTH} characters.")
    local = list(
        Cadastre.objects.prefetch_related("owners")
        .filter(Q(id__icontains=query) | Q(name__icontains=query) | Q(address__icontains=query))
        .order_by("id")[: settings.FORESTIQ_MAP_SEARCH_RESULT_LIMIT]
    )
    allowed = [item for item in local if any(can_access_owner(request, owner) for owner in item.owners.all())]
    if allowed:
        return Response({"source": "LOCAL", "results": [_map_search_result(item) for item in allowed]})

    if not settings.FORESTIQ_INAKS_SEARCH_URL:
        return Response({"source": "IN_AKS", "results": [], "externalConfigured": False})
    if not _inaks_rate_allowed(request):
        return _detail("Address search rate limit exceeded.", status.HTTP_429_TOO_MANY_REQUESTS)

    cache_key = f"p3:inaks:{request_organization_id(request)}:{query.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return Response({"source": "IN_AKS", "results": cached, "externalConfigured": True, "cached": True})

    last_error = None
    for attempt in range(settings.FORESTIQ_MAP_PROXY_RETRIES + 1):
        try:
            response = requests.get(
                settings.FORESTIQ_INAKS_SEARCH_URL,
                params={settings.FORESTIQ_INAKS_QUERY_PARAM: query, "limit": settings.FORESTIQ_MAP_SEARCH_RESULT_LIMIT},
                timeout=settings.FORESTIQ_MAP_PROXY_TIMEOUT_SECONDS,
                headers={"Accept": "application/json", "User-Agent": settings.FORESTIQ_SYNC_USER_AGENT},
            )
            response.raise_for_status()
            if len(response.content) > settings.FORESTIQ_INAKS_MAX_RESPONSE_BYTES:
                return _detail("Address-search response exceeded the size policy.", status.HTTP_502_BAD_GATEWAY)
            payload = response.json()
            raw = (
                payload.get("addresses")
                or payload.get("features")
                or payload.get("results")
                or []
            ) if isinstance(payload, dict) else []
            results = []
            for item in raw[: settings.FORESTIQ_MAP_SEARCH_RESULT_LIMIT]:
                if not isinstance(item, dict):
                    continue
                properties = item.get("properties") if isinstance(item.get("properties"), dict) else item
                geometry = item.get("geometry") if isinstance(item.get("geometry"), dict) else None
                is_cadastre = str(properties.get("liikVal") or "").upper() == "KATASTRIYKSUS"
                cadastral_id = properties.get("katastritunnus") or (properties.get("tunnus") if is_cadastre else None)
                results.append({
                    "id": str(properties.get("adr_id") or properties.get("ads_oid") or properties.get("id") or properties.get("tunnus") or ""),
                    "label": str(properties.get("taisaadress") or properties.get("pikkaadress") or properties.get("aadresstekst") or properties.get("label") or properties.get("name") or ""),
                    "cadastreId": cadastral_id,
                    "address": properties.get("taisaadress") or properties.get("pikkaadress") or properties.get("aadresstekst"),
                    "geometry": geometry,
                    "source": "IN_AKS",
                })
            cache.set(cache_key, results, timeout=settings.FORESTIQ_INAKS_CACHE_SECONDS)
            return Response({"source": "IN_AKS", "results": results, "externalConfigured": True, "cached": False})
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt < settings.FORESTIQ_MAP_PROXY_RETRIES:
                time.sleep(min(0.15 * (2 ** attempt), 0.6))
    return _detail(f"Address search is temporarily unavailable: {last_error}", status.HTTP_502_BAD_GATEWAY)


def _generation_data(item: WfsGeneration | None) -> dict | None:
    if item is None:
        return None
    return {
        "id": str(item.id),
        "sequence": item.sequence,
        "status": item.status,
        "featureCount": item.feature_count,
        "cadastreCount": item.cadastre_count,
        "schemaHash": item.schema_hash or None,
        "validation": item.validation,
        "createdBy": getattr(item.created_by, "id", None),
        "createdAt": int(item.created_at.timestamp() * 1000),
        "observedAt": int(item.observed_at.timestamp() * 1000) if item.observed_at else None,
        "publishedAt": int(item.published_at.timestamp() * 1000) if item.published_at else None,
        "retiredAt": int(item.retired_at.timestamp() * 1000) if item.retired_at else None,
        "schemaDriftApprovedBy": getattr(item.schema_drift_approved_by, "id", None),
        "schemaDriftReason": item.schema_drift_reason or None,
    }


def _manifest_data(item: WfsLayerManifest) -> dict:
    active = item.generations.filter(status=WfsGeneration.Status.ACTIVE).first()
    latest = item.generations.first()
    rollback = item.generations.filter(status=WfsGeneration.Status.RETIRED).first()
    observed_at = active.observed_at if active else None
    stale = (
        observed_at is None
        or (timezone.now() - observed_at).total_seconds() > settings.FORESTIQ_INTEGRATION_STALE_AFTER_SECONDS
    )
    if latest and latest.status == WfsGeneration.Status.FAILED:
        health = "FAILED"
    elif active is None:
        health = "NO_ACTIVE_GENERATION"
    elif stale:
        health = "STALE"
    else:
        health = "HEALTHY"
    return {
        "id": str(item.id),
        "key": item.key,
        "sourceLayer": item.source_layer,
        "cadastreField": item.cadastre_field,
        "enabled": item.enabled,
        "allowSchemaDrift": item.allow_schema_drift,
        "expectedSchemaHash": item.expected_schema_hash or None,
        "expectedSchemaFields": item.expected_schema_fields,
        "retentionGenerations": item.retention_generations,
        "lastVerifiedAt": int(item.last_verified_at.timestamp() * 1000) if item.last_verified_at else None,
        "health": health,
        "freshnessAt": int(observed_at.timestamp() * 1000) if observed_at else None,
        "activeGeneration": _generation_data(active),
        "latestGeneration": _generation_data(latest),
        "rollbackGeneration": _generation_data(rollback),
    }


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def admin_wfs_layers(request):
    if request.method == "GET":
        ensure_default_manifests(organization_id=request_organization_id(request))
        records = WfsLayerManifest.objects.prefetch_related("generations").all()
        return Response([_manifest_data(item) for item in records])

    key = str(request.data.get("key", "")).strip().lower()
    source_layer = str(request.data.get("sourceLayer", "")).strip()
    if not key or not source_layer:
        return _detail("key and sourceLayer are required.")
    item = WfsLayerManifest.objects.create(
        key=key,
        source_layer=source_layer,
        cadastre_field=str(request.data.get("cadastreField", "katastri_nr")).strip() or "katastri_nr",
        enabled=bool(request.data.get("enabled", True)),
        allow_schema_drift=bool(request.data.get("allowSchemaDrift", False)),
        retention_generations=min(max(int(request.data.get("retentionGenerations", 2)), 1), 20),
    )
    return Response(_manifest_data(item), status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAdmin])
def admin_wfs_layer_detail(request, manifest_id):
    item = get_object_or_404(WfsLayerManifest, id=manifest_id)
    if "enabled" in request.data:
        if not isinstance(request.data["enabled"], bool):
            return _detail("enabled must be a boolean.")
        item.enabled = request.data["enabled"]
    if "allowSchemaDrift" in request.data:
        if not isinstance(request.data["allowSchemaDrift"], bool):
            return _detail("allowSchemaDrift must be a boolean.")
        item.allow_schema_drift = request.data["allowSchemaDrift"]
    if "cadastreField" in request.data:
        item.cadastre_field = str(request.data["cadastreField"]).strip()
    if "retentionGenerations" in request.data:
        try:
            item.retention_generations = min(max(int(request.data["retentionGenerations"]), 1), 20)
        except (TypeError, ValueError):
            return _detail("retentionGenerations must be an integer.")
    item.save()
    return Response(_manifest_data(item))


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_wfs_layer_refresh(request, manifest_id):
    from forestry.tasks import refresh_wfs_generation

    item = get_object_or_404(WfsLayerManifest, id=manifest_id)
    if not item.enabled:
        return _detail("This WFS layer is disabled.", status.HTTP_409_CONFLICT)
    result = refresh_wfs_generation.delay(str(request_organization_id(request)), str(item.id), request.user.id)
    return Response({"queued": True, "taskId": str(result.id), "manifest": _manifest_data(item)}, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_wfs_refresh_all(request):
    from forestry.tasks import refresh_all_wfs_generations

    ensure_default_manifests(organization_id=request_organization_id(request))
    result = refresh_all_wfs_generations.delay(str(request_organization_id(request)), request.user.id)
    return Response({"queued": True, "taskId": str(result.id)}, status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_wfs_layer_verify(request, manifest_id):
    item = get_object_or_404(WfsLayerManifest, id=manifest_id)
    result = deep_verify(item)
    return Response({"manifest": _manifest_data(item), "verification": result})


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_wfs_generation_approve(request, generation_id):
    generation = get_object_or_404(WfsGeneration.objects.select_related("manifest"), id=generation_id)
    try:
        generation = approve_schema_drift(
            generation,
            actor=request.user,
            reason=str(request.data.get("reason", "")),
        )
    except ValueError as exc:
        return _detail(str(exc), status.HTTP_409_CONFLICT)
    return Response(_generation_data(generation))


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_wfs_generation_publish(request, generation_id):
    generation = get_object_or_404(WfsGeneration.objects.select_related("manifest"), id=generation_id)
    try:
        generation = publish_generation(generation)
    except (ValueError, ExternalSourceError) as exc:
        return _detail(str(exc), status.HTTP_409_CONFLICT)
    return Response(_generation_data(generation))


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_wfs_generation_rollback(request, generation_id):
    generation = get_object_or_404(WfsGeneration.objects.select_related("manifest"), id=generation_id)
    try:
        generation = rollback_generation(generation)
    except (ValueError, ExternalSourceError) as exc:
        return _detail(str(exc), status.HTTP_409_CONFLICT)
    return Response(_generation_data(generation))


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_wfs_layer_cleanup(request, manifest_id):
    item = get_object_or_404(WfsLayerManifest, id=manifest_id)
    removed = cleanup_retired_generations(item)
    return Response({"removed": removed, "manifest": _manifest_data(item)})
