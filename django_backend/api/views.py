"""ForestIQ REST endpoints implemented with Django ORM and PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timedelta
from io import BytesIO
from hashlib import sha256
import json
from urllib.parse import urlencode
from uuid import uuid4

from django.conf import settings
from django.db import connection, transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDay, TruncHour, TruncMonth, TruncWeek
from django.contrib.gis.geos import Polygon
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema

from accounts.models import Privilege, PrivilegeCode, User
from accounts.authorization import sync_user_groups
from forestry.models import (
    Cadastre,
    CadastreLabel,
    CadastreNotification,
    CadastreSubPart,
    ForestRegistryFeature,
    DataSyncRun,
    Owner,
    OwnerFollowing,
    OwnerLog,
    OwnerStatus,
    OwnerStatusChange,
)
from operations.models import ApplicationMessage, Contract, ContractHistory, Deal, DealStage, DirectMessage, InheritanceCase, PersonDump, Reminder

from .concurrency import delete_if_current, missing_version_response, requested_version, update_if_current, version_conflict_response
from .organization import organization_user_or_404, organization_users, request_organization_id
from .permissions import (
    CanEvaluate,
    CanManageOwners,
    CanManageSales,
    CanUseAssignedOwners,
    CanUsePhones,
    CanViewOrganizationData,
    IsAdmin,
    can_access_owner,
    has_membership_privilege,
)
from .serializers import (
    cadastre_data,
    json_value,
    message_data,
    notification_data,
    owner_data,
    owner_log_data,
    owner_data,
    owner_log_data,
    owner_status_data,
    owner_summary,
    reminder_data,
    user_data,
)
from forestry.tasks import enqueue_cadastre_sync
from forestry.services.tile_cache import cache_vector_tile, get_cached_vector_tile, vector_tile_cache_key


def _detail(message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> Response:
    return Response({"detail": message}, status=http_status)


def _statistics_boundary(value: str | None, *, parameter: str, inclusive_day_end: bool = False) -> datetime | None:
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{parameter} must be an ISO-8601 date or datetime.") from exc
        if inclusive_day_end and len(value) == 10:
            parsed += timedelta(days=1)
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _sync_run_data(run: DataSyncRun) -> dict:
    return {
        "id": run.id,
        "cadastre": run.cadastre_id,
        "taskId": run.task_id,
        "correlationId": run.correlation_id or None,
        "source": run.source,
        "status": run.status,
        "pagesProcessed": run.pages_processed,
        "rowsProcessed": run.rows_processed,
        "retryCount": run.retry_count,
        "backlogSize": run.backlog_size,
        "cursor": run.cursor,
        "lagSeconds": run.lag_seconds,
        "retryOf": run.retry_of_id,
        "startedAt": run.started_at,
        "finishedAt": run.finished_at,
        "result": run.result,
        "error": run.error_message,
    }


@api_view(["GET"])
@permission_classes([IsAdmin])
def sync_runs(request):
    """Return the recent audit trail for administrator-initiated source refreshes."""
    runs = DataSyncRun.objects.select_related("cadastre", "requested_by").all()[:100]
    return Response({"results": [_sync_run_data(run) for run in runs]})


@api_view(["POST"])
@permission_classes([IsAdmin])
def cadastre_sync(request, cadastre_id: str):
    """Queue one cadastral unit's source refresh through Celery."""
    cadastre = get_object_or_404(Cadastre, id=cadastre_id)
    dispatch = enqueue_cadastre_sync(
        cadastre.id,
        organization_id=str(request_organization_id(request)),
        requested_by_id=request.user.id,
        source="api",
    )
    if dispatch.already_running:
        return Response(
            {
                "code": "already_running",
                "detail": "A synchronization run is already active for this cadastre.",
                "run": _sync_run_data(dispatch.run) if dispatch.run else None,
            },
            status=status.HTTP_409_CONFLICT,
        )
    return Response(_sync_run_data(dispatch.run), status=status.HTTP_202_ACCEPTED)


@api_view(["POST"])
@permission_classes([IsAdmin])
def retry_sync_run(request, run_id: int):
    """Requeue only the failed source parts of a terminal cadastre synchronization."""

    run = get_object_or_404(DataSyncRun, id=run_id)
    if run.status not in (DataSyncRun.Status.PARTIAL, DataSyncRun.Status.FAILED):
        return _detail("Only PARTIAL or FAILED synchronization runs can be retried.", status.HTTP_409_CONFLICT)
    if run.cadastre is None:
        return _detail("This audit run has no cadastre-scoped source part to retry.", status.HTTP_409_CONFLICT)
    failed_sources = run.result.get("failed_sources", {}) if isinstance(run.result, dict) else {}
    source_names = tuple(source for source in failed_sources if source in {"cadastre_wfs", "metsaregister_wfs", "soos_wfs", "parimus_inheritance"})
    if not source_names:
        return _detail("The audit run has no recorded failed source part to retry.", status.HTTP_409_CONFLICT)
    if run.retry_count >= settings.FORESTIQ_SYNC_RUN_MAX_RETRIES:
        return _detail("The synchronization retry limit has been reached.", status.HTTP_409_CONFLICT)
    dispatch = enqueue_cadastre_sync(
        run.cadastre_id,
        organization_id=str(request_organization_id(request)),
        requested_by_id=request.user.id,
        source=f"retry:{run.source}",
        source_names=source_names,
    )
    if dispatch.already_running or dispatch.run is None:
        return Response(
            {"code": "already_running", "detail": "A synchronization run is already active for this cadastre.", "run": _sync_run_data(dispatch.run) if dispatch.run else None},
            status=status.HTTP_409_CONFLICT,
        )
    retry = dispatch.run
    retry.retry_of = run
    retry.retry_count = run.retry_count + 1
    retry.backlog_size = DataSyncRun.objects.filter(status__in=(DataSyncRun.Status.QUEUED, DataSyncRun.Status.RUNNING)).count()
    retry.save(update_fields=("retry_of", "retry_count", "backlog_size"))
    return Response(_sync_run_data(retry), status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def cadastre_map_features(request):
    """Return validated cadastral geometries as WGS84 GeoJSON for MapLibre."""
    cadastres = _map_cadastre_queryset(request)
    viewport, error = _map_viewport(request)
    if error:
        return error
    if viewport:
        cadastres = cadastres.filter(boundary__intersects=viewport)
    features = []
    for cadastre in cadastres.order_by("id")[:_map_limit(request, settings.FORESTIQ_MAP_CADASTRE_LIMIT)]:
        geometry = cadastre.boundary.clone()
        geometry.transform(4326)
        features.append({"type": "Feature", "id": cadastre.id, "geometry": json.loads(geometry.json), "properties": {"id": cadastre.id, "name": cadastre.name, "county": cadastre.county, "area": str(cadastre.area or "")}})
    return Response({"type": "FeatureCollection", "features": features})


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def map_layer_features(request, layer: str):
    """Return validated GeoDjango layers as WGS84 GeoJSON for the MapLibre client."""

    layer = layer.lower()
    if layer not in {"subparts", "new-subparts", "registry", "notifications"}:
        return _detail("Unknown map layer.", status.HTTP_404_NOT_FOUND)
    viewport, error = _map_viewport(request)
    if error:
        return error
    cadastres = _map_cadastre_queryset(request)
    features = []
    if layer in {"subparts", "new-subparts"}:
        records = CadastreSubPart.objects.exclude(boundary__isnull=True).filter(cadastre__in=cadastres).select_related("cadastre").order_by("cadastre_id", "sub_part_code")
        if viewport:
            records = records.filter(boundary__intersects=viewport)
        if layer == "new-subparts":
            since = timezone.now() - timedelta(hours=settings.FORESTIQ_MAP_NEW_SUBPART_HOURS)
            records = records.filter(discovered_at__gte=since)
        for record in records[:_map_limit(request, settings.FORESTIQ_MAP_FEATURE_LIMIT)]:
            geometry = record.boundary.clone()
            geometry.transform(4326)
            features.append({"type": "Feature", "id": f"{record.cadastre_id}:{record.sub_part_code}", "geometry": json.loads(geometry.json), "properties": {"id": f"{record.cadastre_id}:{record.sub_part_code}", "cadastreId": record.cadastre_id, "subpartCode": record.sub_part_code, "treeType": record.tree_type_code, "area": str(record.area or ""), "discoveredAt": record.discovered_at.isoformat() if record.discovered_at else ""}})
    elif layer == "registry":
        records = ForestRegistryFeature.objects.exclude(spatial_geometry__isnull=True).filter(cadastre__in=cadastres).select_related("cadastre").order_by("cadastre_id", "source_layer", "source_id")
        if viewport:
            records = records.filter(spatial_geometry__intersects=viewport)
        for record in records[:_map_limit(request, settings.FORESTIQ_MAP_FEATURE_LIMIT)]:
            geometry = record.spatial_geometry.clone()
            geometry.transform(4326)
            features.append({"type": "Feature", "id": f"{record.source_layer}:{record.source_id}", "geometry": json.loads(geometry.json), "properties": {"id": f"{record.source_layer}:{record.source_id}", "cadastreId": record.cadastre_id, "subpartCode": record.subpart_code, "title": record.title, "workCode": record.work_code, "decision": record.decision, "area": str(record.area or "")}})
    else:
        records = CadastreNotification.objects.exclude(cadastre_subpart_code__isnull=True).filter(cadastre__in=cadastres).select_related("cadastre").order_by("-registration_date", "-id")
        subparts = CadastreSubPart.objects.exclude(boundary__isnull=True).filter(cadastre__in=cadastres)
        if viewport:
            subparts = subparts.filter(boundary__intersects=viewport)
            records = records.filter(cadastre_id__in=subparts.values("cadastre_id"))
        subpart_lookup = {(item.cadastre_id, item.sub_part_code): item for item in subparts}
        for record in records[:_map_limit(request, settings.FORESTIQ_MAP_FEATURE_LIMIT)]:
            subpart = subpart_lookup.get((record.cadastre_id, record.cadastre_subpart_code))
            if not subpart:
                continue
            geometry = subpart.boundary.centroid
            geometry.transform(4326)
            features.append({"type": "Feature", "id": str(record.id), "geometry": json.loads(geometry.json), "properties": {"id": str(record.id), "cadastreId": record.cadastre_id, "subpartCode": record.cadastre_subpart_code, "notificationNumber": record.notification_number, "workCode": record.work_code, "state": record.state, "registrationDate": record.registration_date.isoformat() if record.registration_date else "", "treeType": subpart.tree_type_code, "subpartArea": str(subpart.area or ""), "discoveredAt": subpart.discovered_at.isoformat() if subpart.discovered_at else ""}})
    return Response({"type": "FeatureCollection", "features": features})


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def map_vector_tile(request, layer: str, z: int, x: int, y: int):
    """Return an organization-scoped Mapbox Vector Tile from PostGIS geometry."""

    layer = layer.lower()
    if layer not in {"cadastres", "subparts", "registry"}:
        return _detail("Unknown vector tile layer.", status.HTTP_404_NOT_FOUND)
    coordinates, error = _map_tile_coordinates(z, x, y)
    if error:
        return error
    if connection.vendor != "postgresql":
        return _detail("Vector tiles require a PostGIS database.", status.HTTP_501_NOT_IMPLEMENTED)

    cadastres = _map_cadastre_queryset(request)
    if layer == "cadastres":
        queryset = cadastres.exclude(boundary__isnull=True)
        properties = ("id", "name", "county", "municipality", "area")
        geometry_field = "boundary"
    elif layer == "subparts":
        queryset = CadastreSubPart.objects.exclude(boundary__isnull=True).filter(cadastre__in=cadastres)
        properties = ("id", "cadastre_id", "sub_part_code", "tree_type_code", "area")
        geometry_field = "boundary"
    else:
        queryset = ForestRegistryFeature.objects.exclude(spatial_geometry__isnull=True).filter(cadastre__in=cadastres)
        properties = ("id", "cadastre_id", "subpart_code", "title", "work_code", "decision", "area", "volume")
        geometry_field = "spatial_geometry"

    organization_id = str(request_organization_id(request))
    cache_key = vector_tile_cache_key(
        organization_id=organization_id,
        layer=layer,
        z=z,
        x=x,
        y=y,
        query_fingerprint=_tile_query_fingerprint(request),
    )
    tile = get_cached_vector_tile(cache_key)
    if tile is None:
        tile = _map_vector_tile_bytes(queryset, properties, geometry_field, layer, *coordinates)
        cache_vector_tile(cache_key, tile)

    etag = f'"{sha256(tile).hexdigest()}"'
    if _if_none_match_matches(request.headers.get("If-None-Match", ""), etag):
        response = HttpResponse(status=status.HTTP_304_NOT_MODIFIED)
    else:
        response = HttpResponse(tile, content_type="application/vnd.mapbox-vector-tile")
    response["ETag"] = etag
    response["Cache-Control"] = f"private, max-age={settings.FORESTIQ_MVT_CACHE_TTL_SECONDS}, must-revalidate"
    response["Vary"] = "Authorization"
    return response


def _tile_query_fingerprint(request) -> str:
    """Canonicalize only supported map filters and include the access principal.

    Organization scoping alone is insufficient because non-admins receive only their
    assigned owners' cadastres. The principal makes cached payloads safe across roles.
    """

    filters = []
    for key in ("customer", "activeDeal", "activityDays", "dealStage"):
        value = request.query_params.get(key)
        if value:
            filters.append((key, value))
    filters.sort()
    return f"user={request.user.pk}&{urlencode(filters)}"


def _if_none_match_matches(header: str, etag: str) -> bool:
    """Return whether a standard strong or weak conditional validator matches."""

    for candidate in header.split(","):
        candidate = candidate.strip()
        if candidate == "*" or candidate.removeprefix("W/") == etag:
            return True
    return False


def _map_tile_coordinates(z: int, x: int, y: int):
    if not 0 <= z <= 22:
        return None, _detail("z must be between 0 and 22.")
    maximum = 2**z
    if not 0 <= x < maximum or not 0 <= y < maximum:
        return None, _detail("x and y must be valid coordinates for z.")
    return (z, x, y), None


def _map_vector_tile_bytes(queryset, properties: tuple[str, ...], geometry_field: str, layer: str, z: int, x: int, y: int) -> bytes:
    """Compile a scoped queryset into a single PostGIS ST_AsMVT query."""

    source_sql, source_params = queryset.values(*properties, geometry_field).query.sql_with_params()
    property_columns = ", ".join(properties)
    sql = f"""
        WITH source AS ({source_sql}),
        tile_features AS (
            SELECT {property_columns},
                ST_AsMVTGeom(
                    ST_Transform({geometry_field}, 3857),
                    ST_TileEnvelope(%s, %s, %s),
                    4096,
                    64,
                    true
                ) AS geom
            FROM source
        )
        SELECT COALESCE(ST_AsMVT(tile_features, %s, 4096, 'geom'), ''::bytea)
        FROM tile_features
        WHERE geom IS NOT NULL
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [*source_params, z, x, y, layer])
        result = cursor.fetchone()
    return bytes(result[0] if result and result[0] else b"")


def _map_viewport(request):
    raw_bbox = request.query_params.get("bbox", "").strip()
    if not raw_bbox:
        return None, None
    try:
        west, south, east, north = (float(value) for value in raw_bbox.split(","))
        if west >= east or south >= north or west < -180 or east > 180 or south < -90 or north > 90:
            raise ValueError
        viewport = Polygon.from_bbox((west, south, east, north))
        viewport.srid = 4326
        viewport.transform(3301)
        return viewport, None
    except ValueError:
        return None, _detail("bbox must contain west,south,east,north in EPSG:4326")


def _map_limit(request, default: int) -> int:
    try:
        requested = int(request.query_params.get("limit", default))
    except (TypeError, ValueError):
        requested = default
    return max(1, min(requested, settings.FORESTIQ_MAP_MAX_FEATURE_LIMIT))


def _map_cadastre_queryset(request):
    """Filter map geometries by access and the commercial/activity filters selected in MapLibre."""
    cadastres = Cadastre.objects.exclude(boundary__isnull=True)
    if not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        cadastres = cadastres.filter(owners__assignee=request.user)
    if request.query_params.get("customer") in {"1", "true"}:
        cadastres = cadastres.filter(owners__deals__stage=DealStage.WON)
    if request.query_params.get("activeDeal") in {"1", "true"}:
        cadastres = cadastres.filter(deals__stage__in=[DealStage.QUALIFICATION, DealStage.EVALUATION, DealStage.NEGOTIATION])
    stages = [stage.strip().upper() for stage in request.query_params.get("dealStage", "").split(",") if stage.strip()]
    valid_stages = {choice for choice, _ in DealStage.choices}
    if stages:
        cadastres = cadastres.filter(deals__stage__in=[stage for stage in stages if stage in valid_stages])
    try:
        activity_days = int(request.query_params.get("activityDays", "0"))
    except ValueError:
        activity_days = 0
    if activity_days:
        since = timezone.now() - timedelta(days=max(1, min(activity_days, 730)))
        cadastres = cadastres.filter(Q(owners__logs__created_at__gte=since) | Q(owners__reminders__created_time__gte=since) | Q(deals__updated_at__gte=since))
    return cadastres.distinct()


def _parse_millis(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.get_current_timezone())
    if isinstance(value, str) and value.isdigit():
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.get_current_timezone())
    if isinstance(value, str):
        return parse_datetime(value.replace("Z", "+00:00"))
    return None


def _owner_or_forbidden(request, owner_id: str):
    owner = get_object_or_404(Owner.objects.select_related("assignee").prefetch_related("cadastres"), id=owner_id)
    if not can_access_owner(request, owner):
        return None, _detail("You do not have access to this owner.", status.HTTP_403_FORBIDDEN)
    return owner, None


def _user_payload(user: User) -> dict:
    return {"id": user.id, "name": user.full_name, "privileges": user.privilege_codes}


def _paginate(queryset, request):
    try:
        page = max(int(request.query_params.get("page", "0")), 0)
        size = min(max(int(request.query_params.get("size", "50")), 1), 200)
    except ValueError:
        page, size = 0, 50
    return queryset[page * size : (page + 1) * size]


def _owner_queryset(request):
    queryset = Owner.objects.select_related("assignee").prefetch_related("cadastres")
    if not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        queryset = queryset.filter(assignee=request.user)
    for field in ("id", "name", "phone", "email"):
        value = request.query_params.get(field)
        if value:
            queryset = queryset.filter(**{f"{field}__icontains": value})
    cadastre = request.query_params.get("cadastre")
    if cadastre:
        queryset = queryset.filter(cadastres__id__icontains=cadastre)
    statuses = request.query_params.get("statuses")
    if statuses:
        queryset = queryset.filter(status__in=[item for item in statuses.split(",") if item])
    return queryset.distinct()


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def service_status(request):
    return Response({"status": "OK", "service": "forestiq-django", "time": int(timezone.now().timestamp() * 1000)})


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def admin_users(request):
    if request.method == "GET":
        return Response([_user_payload(user) for user in organization_users(request).prefetch_related("privilege_assignments")])

    user_id = str(request.data.get("id", "")).strip()
    full_name = str(request.data.get("name", "")).strip()
    password = request.data.get("password")
    privileges = request.data.get("privileges", [])
    if not user_id or not full_name or not password:
        return _detail("id, name and password are required.")
    if User.objects.filter(id=user_id).exists():
        return _detail("A user with that id already exists.", status.HTTP_409_CONFLICT)
    with transaction.atomic():
        user = User.objects.create_user(user_id, full_name, password, default_organization_id=request_organization_id(request))
        Privilege.objects.bulk_create([Privilege(user=user, code=code) for code in privileges if code in PrivilegeCode.values])
        sync_user_groups(user)
    return Response(_user_payload(user), status=status.HTTP_201_CREATED)


@api_view(["POST", "DELETE"])
@permission_classes([IsAdmin])
def admin_user_detail(request, user_id: str):
    user = organization_user_or_404(request, user_id)
    if request.method == "DELETE":
        if user.id == request.user.id:
            return _detail("You cannot delete the current user.")
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    full_name = request.data.get("name")
    if full_name:
        user.full_name = str(full_name).strip()
        user.save(update_fields=["full_name"])
    if "privileges" in request.data:
        privilege_codes = [code for code in request.data["privileges"] if code in PrivilegeCode.values]
        Privilege.objects.filter(user=user).delete()
        Privilege.objects.bulk_create([Privilege(user=user, code=code) for code in privilege_codes])
    return Response(_user_payload(user))


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def owner_statuses(request):
    if request.method == "GET":
        return Response([owner_status_data(item) for item in OwnerStatus.objects.all()])
    data = request.data
    status_id = str(data.get("id", "")).strip()
    if not status_id:
        return _detail("Status id is required.")
    owner_status, _ = OwnerStatus.objects.update_or_create(
        id=status_id,
        defaults={
            "color_hex": str(data.get("colorHex", "ed7a6f")).lstrip("#"),
            "days_out_of_search": int(data.get("durationDays", 0)),
            "protected": bool(data.get("protectedStatus", False)),
        },
    )
    return Response(owner_status_data(owner_status))


@api_view(["DELETE"])
@permission_classes([IsAdmin])
def owner_status_detail(request, status_id: str):
    owner_status = get_object_or_404(OwnerStatus, id=status_id)
    if owner_status.protected:
        return _detail("Protected status cannot be deleted.", status.HTTP_409_CONFLICT)
    if Owner.objects.filter(status=status_id).exists():
        return _detail("Status is currently used by owners.", status.HTTP_409_CONFLICT)
    owner_status.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([CanManageOwners])
def owner_list(request):
    return Response([owner_summary(owner) for owner in _owner_queryset(request)])


@api_view(["GET", "POST"])
@permission_classes([CanManageOwners])
def owner_detail(request, owner_id: str):
    owner, denied = _owner_or_forbidden(request, owner_id)
    if denied:
        return denied
    if request.method == "GET":
        return Response(owner_data(owner))

    editable = ("name", "type", "phone", "email", "address", "info", "out_of_admin_search_reason")
    changes = {field: request.data[field] or "" for field in editable if field in request.data}
    if not changes:
        return Response(owner_data(owner))
    expected_version = requested_version(request)
    if expected_version is None:
        return missing_version_response()
    updated_owner = update_if_current(owner, expected_version, **changes)
    if updated_owner is None:
        owner.refresh_from_db(fields=["version"])
        return version_conflict_response(owner, expected_version)
    return Response(owner_data(updated_owner))


@api_view(["POST"])
@permission_classes([CanManageOwners])
def owner_add(request, owner_id: str):
    if not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        return _detail("Owner creation requires OWNER_PROFILE.", status.HTTP_403_FORBIDDEN)
    if Owner.objects.filter(id=owner_id).exists():
        return _detail("Owner already exists.", status.HTTP_409_CONFLICT)
    owner = Owner.objects.create(
        id=owner_id,
        name=str(request.data.get("ownerName") or request.data.get("name") or "").strip(),
        type=str(request.data.get("ownerType") or request.data.get("type") or "PERSON"),
    )
    if not owner.name:
        owner.delete()
        return _detail("Owner name is required.")
    return Response(owner_data(owner), status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([CanManageOwners])
def owner_status(request, owner_id: str):
    owner, denied = _owner_or_forbidden(request, owner_id)
    if denied:
        return denied
    if request.method == "GET":
        return Response(
            {
                "possibleAssignees": [user_data(user) for user in organization_users(request, active_only=True)],
                "possibleOwnerStatuses": list(OwnerStatus.objects.values_list("id", flat=True)),
                "status": owner.status,
                "assignee": user_data(owner.assignee),
            }
        )
    new_status = str(request.data.get("code", "")).strip()
    if not OwnerStatus.objects.filter(id=new_status).exists():
        return _detail("Unknown owner status.")
    expected_version = requested_version(request)
    if expected_version is None:
        return missing_version_response()
    old_status = owner.status
    updated_owner = update_if_current(owner, expected_version, status=new_status, status_set_at=timezone.now())
    if updated_owner is None:
        owner.refresh_from_db(fields=["version"])
        return version_conflict_response(owner, expected_version)
    OwnerStatusChange.objects.create(user=request.user, from_status=old_status, to_status=new_status)
    return Response(owner_data(updated_owner))


@api_view(["POST"])
@permission_classes([IsAdmin])
def owner_assignee(request, owner_id: str):
    owner = get_object_or_404(Owner, id=owner_id)
    assignee_id = request.data.get("assignee")
    assignee = organization_user_or_404(request, assignee_id) if assignee_id else None
    expected_version = requested_version(request)
    if expected_version is None:
        return missing_version_response()
    updated_owner = update_if_current(owner, expected_version, assignee=assignee)
    if updated_owner is None:
        owner.refresh_from_db(fields=["version"])
        return version_conflict_response(owner, expected_version)
    return Response(owner_data(updated_owner))


@api_view(["GET", "POST"])
@permission_classes([CanUseAssignedOwners])
def owner_log(request, owner_id: str):
    owner, denied = _owner_or_forbidden(request, owner_id)
    if denied:
        return denied
    if request.method == "GET":
        return Response([owner_log_data(entry) for entry in owner.logs.select_related("creator").all()])
    message = str(request.data.get("message", "")).strip()
    if not message:
        return _detail("Log message is required.")
    OwnerLog.objects.create(owner=owner, creator=request.user, message=message)
    return Response([owner_log_data(entry) for entry in owner.logs.select_related("creator").all()])


@api_view(["POST"])
@permission_classes([CanUseAssignedOwners])
def mark_cadastres(request, owner_id: str):
    owner, denied = _owner_or_forbidden(request, owner_id)
    if denied:
        return denied
    selected_ids = request.data if isinstance(request.data, list) else request.data.get("cadastres", [])
    owner.cadastres.update(marked=False)
    owner.cadastres.filter(id__in=selected_ids).update(marked=True)
    return Response(owner_data(owner))


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def cadastre_detail(request, cadastre_id: str):
    cadastre = get_object_or_404(Cadastre.objects.prefetch_related("owners", "labels", "sub_parts"), id=cadastre_id)
    owners = cadastre.owners.select_related("assignee")
    if not any(can_access_owner(request, owner) for owner in owners):
        return _detail("You do not have access to this cadastre.", status.HTTP_403_FORBIDDEN)
    return Response(cadastre_data(cadastre))


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def cadastre_summary(request, cadastre_id: str):
    """Return compact, access-controlled counters for a cadastral unit.

    The endpoint deliberately avoids the expensive activity and object payloads used by
    the map workspace. It is therefore appropriate for map side-panels and performance
    budgets that must remain predictable at portfolio scale.
    """

    cadastre = get_object_or_404(Cadastre.objects, id=cadastre_id)
    owners = [owner for owner in cadastre.owners.all() if can_access_owner(request, owner)]
    if not owners:
        return _detail("You do not have access to this cadastre.", status.HTTP_403_FORBIDDEN)

    owner_ids = [owner.id for owner in owners]
    deals = Deal.objects.filter(owner_id__in=owner_ids, parcels=cadastre).distinct()
    closed_stages = [DealStage.WON, DealStage.LOST, DealStage.CANCELLED]
    subpart_totals = cadastre.sub_parts.aggregate(count=Count("id"), area=Sum("area"))
    notification_totals = cadastre.notifications.aggregate(
        count=Count("id"),
        active_count=Count("id", filter=Q(archived=False)),
    )
    stage_counts = {item["stage"]: item["count"] for item in deals.values("stage").annotate(count=Count("id"))}
    customer_owners = [owner for owner in owners if deals.filter(owner=owner, stage=DealStage.WON).exists()]

    return Response(
        {
            "cadastre": {"id": cadastre.id, "name": cadastre.name, "area": json_value(cadastre.area)},
            "owners": {"count": len(owners), "customerCount": len(customer_owners)},
            "subparts": {"count": subpart_totals["count"], "area": json_value(subpart_totals["area"])},
            "notifications": {"count": notification_totals["count"], "activeCount": notification_totals["active_count"]},
            "customerRelationship": {
                "isCustomer": bool(customer_owners),
                "activeDealCount": deals.exclude(stage__in=closed_stages).count(),
                "wonDealCount": deals.filter(stage=DealStage.WON).count(),
                "dealStages": stage_counts,
            },
        }
    )


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def cadastre_workspace(request, cadastre_id: str):
    """Return an access-controlled, map-first workspace payload for one cadastral unit."""

    cadastre = get_object_or_404(Cadastre.objects.prefetch_related("owners", "labels", "sub_parts", "notifications", "registry_features"), id=cadastre_id)
    owners = [owner for owner in cadastre.owners.select_related("assignee").all() if can_access_owner(request, owner)]
    if not owners:
        return _detail("You do not have access to this cadastre.", status.HTTP_403_FORBIDDEN)
    activities = []
    owner_payloads = []
    for owner in owners:
        logs = [owner_log_data(item) | {"ownerId": owner.id, "ownerName": owner.name, "kind": "OWNER_LOG"} for item in owner.logs.select_related("creator").all()[:40]]
        activities.extend(logs)
        reminders = [{"id": str(item.id), "kind": "REMINDER", "ownerId": owner.id, "ownerName": owner.name, "text": item.text, "at": json_value(item.due_time), "createdAt": json_value(item.created_time)} for item in owner.reminders.filter(cadastre__in=("", cadastre.id)).order_by("-due_time")[:20]]
        activities.extend(reminders)
        deals = Deal.objects.filter(owner=owner, parcels=cadastre).distinct().order_by("-updated_at")
        deal_data = [{"id": str(item.id), "stage": item.stage, "saleSubject": item.sale_subject, "priceExpectation": json_value(item.price_expectation), "recommendedPurchasePrice": json_value(item.recommended_purchase_price), "updatedAt": json_value(item.updated_at), "closedAt": json_value(item.closed_at)} for item in deals[:20]]
        activities.extend([{"id": item["id"], "kind": "DEAL", "ownerId": owner.id, "ownerName": owner.name, "text": f"Tehing {item['stage']}", "at": item["updatedAt"]} for item in deal_data])
        owner_payloads.append(owner_data(owner) | {"activityLog": logs, "reminders": reminders, "deals": deal_data, "customerRelationship": {"ownerStatus": owner.status or None, "isCustomer": deals.filter(stage=DealStage.WON).exists(), "activeDealCount": deals.exclude(stage__in=[DealStage.WON, DealStage.LOST, DealStage.CANCELLED]).count(), "wonDealCount": deals.filter(stage=DealStage.WON).count()}})
    activities.sort(key=lambda item: item.get("at") or item.get("createdAt") or 0, reverse=True)
    registry = [{"id": item.id, "title": item.title, "sourceLayer": item.source_layer, "subpartCode": item.subpart_code, "workCode": item.work_code, "decision": item.decision, "area": json_value(item.area), "volume": json_value(item.volume), "eventDate": json_value(item.event_date), "attributes": item.attributes} for item in cadastre.registry_features.all()[:100]]
    return Response({"cadastre": cadastre_data(cadastre), "owners": owner_payloads, "activities": activities[:100], "notifications": [notification_data(item) for item in cadastre.notifications.all()[:100]], "registryFeatures": registry, "customerSummary": {"ownerCount": len(owners), "customerOwnerCount": sum(1 for item in owner_payloads if item["customerRelationship"]["isCustomer"]), "activeDealCount": sum(item["customerRelationship"]["activeDealCount"] for item in owner_payloads)}})


@api_view(["GET", "POST"])
@permission_classes([CanUseAssignedOwners])
def cadastre_evaluation(request, cadastre_id: str):
    cadastre = get_object_or_404(Cadastre, id=cadastre_id)
    if request.method == "GET":
        return Response({"ownerPrice": cadastre.owners_price or None, "ourPrice": cadastre.our_price or None})
    cadastre.owners_price = str(request.data.get("ownerPrice", ""))
    cadastre.our_price = str(request.data.get("ourPrice", ""))
    cadastre.save(update_fields=["owners_price", "our_price"])
    return Response({"ownerPrice": cadastre.owners_price, "ourPrice": cadastre.our_price})


@api_view(["GET", "POST", "DELETE"])
@permission_classes([CanUseAssignedOwners])
def cadastre_label(request, cadastre_id: str, label: str | None = None):
    cadastre = get_object_or_404(Cadastre, id=cadastre_id)
    if request.method == "GET":
        return Response({"labels": list(cadastre.labels.values_list("code", flat=True))})
    if not label:
        return _detail("Label is required.")
    if request.method == "POST":
        CadastreLabel.objects.get_or_create(cadastre=cadastre, code=label)
    else:
        CadastreLabel.objects.filter(cadastre=cadastre, code=label).delete()
    return Response({"labels": list(cadastre.labels.values_list("code", flat=True))})


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def cadastre_notifications(request, cadastre_id: str):
    cadastre = get_object_or_404(Cadastre, id=cadastre_id)
    records = cadastre.notifications.all()
    if request.query_params.get("includeArchived", "false").lower() != "true":
        records = records.filter(archived=False)
    return Response([notification_data(item) for item in records])


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def cadastre_mkdata(request, cadastre_id: str):
    cadastre = get_object_or_404(Cadastre, id=cadastre_id)
    return Response(
        {
            "cadastreNo": cadastre.id,
            "registrationDate": json_value(cadastre.mk_date),
            "sections": [
                {"sectionNo": part.sub_part_code, "treeSpecies": part.tree_type_code, "area": json_value(part.area), "polygon": part.polygon}
                for part in cadastre.sub_parts.all()
            ],
        }
    )


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def cadastre_areas(request, cadastre_id: str):
    cadastre = get_object_or_404(Cadastre, id=cadastre_id)
    return Response(
        {
            "area": json_value(cadastre.area),
            "forestArea": json_value(cadastre.forest_area),
            "arableArea": json_value(cadastre.arable_area),
            "yardArea": json_value(cadastre.yard_area),
            "meadowArea": json_value(cadastre.meadow_area),
            "underWaterArea": json_value(cadastre.underwater_area),
            "buildingsArea": json_value(cadastre.buildings_area),
            "otherArea": json_value(cadastre.other_area),
        }
    )


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def registry_features(request, cadastre_id: str):
    records = ForestRegistryFeature.objects.filter(cadastre_id=cadastre_id)
    return Response(
        [
            {
                "id": record.id,
                "sourceLayer": record.source_layer,
                "sourceId": record.source_id,
                "cadastreId": record.cadastre_id,
                "subpartCode": record.subpart_code,
                "title": record.title,
                "workCode": record.work_code,
                "decision": record.decision,
                "area": json_value(record.area),
                "volume": json_value(record.volume),
                "eventDate": json_value(record.event_date),
                "attributes": record.attributes,
                "geometry": record.geometry,
            }
            for record in records
        ]
    )


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def my_work(request):
    return Response([owner_summary(owner) for owner in _owner_queryset(request).filter(assignee=request.user)])


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def next_owner(request):
    owner = _owner_queryset(request).filter(assignee=request.user).order_by("status_set_at", "id").first()
    if not owner:
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({"id": owner.id})


@api_view(["GET"])
@permission_classes([CanEvaluate])
def owners_in_need_of_evaluation(request):
    return Response([owner_summary(owner) for owner in Owner.objects.select_related("assignee").filter(status="WAITS_FOR_EVALUATION")])


@api_view(["GET"])
@permission_classes([CanManageOwners])
def caller_workdesk_prep(request):
    return Response(
        {
            "statuses": [owner_status_data(item) for item in OwnerStatus.objects.all()],
            "users": [user_data(user) for user in organization_users(request, active_only=True)],
        }
    )


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_workdesk_prep(request):
    return Response(
        {
            "statuses": [owner_status_data(item) for item in OwnerStatus.objects.all()],
            "users": [user_data(user) for user in organization_users(request, active_only=True)],
            "counties": list(Cadastre.objects.exclude(county="").values_list("county", flat=True).distinct()),
            "municipalities": list(Cadastre.objects.exclude(municipality="").values_list("municipality", flat=True).distinct()),
        }
    )


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_workdesk_search(request):
    return Response([owner_summary(owner) for owner in _owner_queryset(request)])


@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_workdesk_assign(request):
    owner_ids = request.data.get("owners", [])
    assignee = organization_user_or_404(request, request.data.get("userId"))
    queryset = Owner.objects.filter(id__in=owner_ids)
    if not request.data.get("reassign", False):
        queryset = queryset.filter(assignee__isnull=True)
    updated = queryset.update(assignee=assignee)
    return Response({"assigned": updated})


@api_view(["GET", "POST"])
@permission_classes([CanManageOwners])
def reminders(request):
    if request.method == "GET":
        records = Reminder.objects.select_related("owner", "owner__assignee", "creator").filter(Q(creator=request.user) | Q(owner__assignee=request.user))
        return Response([reminder_data(item) for item in records.distinct()])
    owner = get_object_or_404(Owner, id=request.data.get("ownerId")) if request.data.get("ownerId") else None
    due_time = _parse_millis(request.data.get("dueTime"))
    if not due_time:
        return _detail("A valid dueTime is required.")
    reminder = Reminder.objects.create(
        owner=owner,
        creator=request.user,
        text=str(request.data.get("text", "")),
        due_time=due_time,
        cadastre=str(request.data.get("cadastre", "")),
        property_name=str(request.data.get("propertyName", "")),
    )
    return Response(reminder_data(reminder), status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([CanManageOwners])
def reminder_detail(request, reminder_id: int):
    reminder = get_object_or_404(Reminder, id=reminder_id)
    if reminder.creator_id != request.user.id and (not reminder.owner or reminder.owner.assignee_id != request.user.id) and not has_membership_privilege(request, PrivilegeCode.ADMIN):
        return _detail("You do not have access to this reminder.", status.HTTP_403_FORBIDDEN)
    reminder.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([CanUseAssignedOwners])
def reminders_dashboard(request):
    records = Reminder.objects.select_related("owner", "owner__assignee", "creator").filter(due_time__lte=timezone.now() + timedelta(days=7))
    if not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        records = records.filter(Q(creator=request.user) | Q(owner__assignee=request.user))
    return Response([reminder_data(item) for item in records])


@api_view(["GET", "POST"])
@permission_classes([CanUsePhones])
def persons_dump(request):
    if request.method == "GET":
        query = request.query_params.get("query", "")
        records = PersonDump.objects.all()
        if query:
            records = records.filter(Q(name__icontains=query) | Q(phone__icontains=query) | Q(code__icontains=query))
        return Response(list(records.values("id", "source", "name", "phone", "address", "code")))
    entry = PersonDump.objects.create(
        source=str(request.data.get("source", "")),
        name=str(request.data.get("name", "")),
        phone=str(request.data.get("phone", "")),
        address=str(request.data.get("address", "")),
        code=str(request.data.get("code", "")),
    )
    return Response({"id": entry.id}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([CanUsePhones])
def persons_dump_detail(request, person_id: int):
    get_object_or_404(PersonDump, id=person_id).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def received_messages(request):
    records = DirectMessage.objects.select_related("sender", "recipient").filter(recipient=request.user)
    return Response([message_data(item) for item in _paginate(records, request)])


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def sent_messages(request):
    records = DirectMessage.objects.select_related("sender", "recipient").filter(sender=request.user)
    return Response([message_data(item) for item in _paginate(records, request)])


@api_view(["POST"])
@permission_classes([CanViewOrganizationData])
def send_message(request):
    recipient = organization_user_or_404(request, request.data.get("recipient"), active_only=True)
    text = str(request.data.get("message", "")).strip()
    if not text:
        return _detail("Message is required.")
    message = DirectMessage.objects.create(sender=request.user, recipient=recipient, text=text)
    return Response(message_data(message), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([CanViewOrganizationData])
def mark_messages_read(request):
    records = DirectMessage.objects.filter(recipient=request.user, noticed_at__isnull=True)
    ids = request.data.get("ids")
    mark_read_until = _parse_millis(request.data.get("markReadUntil"))
    if ids is not None:
        records = records.filter(id__in=ids)
    elif mark_read_until:
        records = records.filter(created_at__lte=mark_read_until)
    updated = records.update(noticed_at=timezone.now())
    return Response({"updated": updated})


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def message_users(request):
    return Response(list(organization_users(request, active_only=True).values_list("id", flat=True)))


@api_view(["GET"])
@permission_classes([CanViewOrganizationData])
def new_messages_count(request):
    return Response({"newMessageCount": DirectMessage.objects.filter(recipient=request.user, noticed_at__isnull=True).count()})


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def contracts(request):
    if request.method == "GET":
        records = list(ContractHistory.objects.all())
        contracts_by_id = {
            item.id: item
            for item in Contract.objects.select_related("template_version").filter(id__in=[record.id for record in records])
        }
        return Response(
            [
                {
                    "id": item.id,
                    "version": contracts_by_id.get(item.id).version if item.id in contracts_by_id else None,
                    "sellers": item.sellers,
                    "buyer": item.buyer,
                    "contractNo": item.contract_number,
                    "created": json_value(item.created_at),
                    "templateVersion": (contracts_by_id[item.id].template_snapshot or None) if item.id in contracts_by_id else None,
                }
                for item in records
            ]
        )
    data = request.data
    contract_id = str(data.get("id") or uuid4())
    with transaction.atomic():
        contract = Contract.objects.filter(id=contract_id).first()
        if contract is None:
            contract = Contract.objects.create(id=contract_id, base_id=data.get("baseId", ""))
        else:
            expected_version = requested_version(request)
            if expected_version is None:
                return missing_version_response()
            updated_contract = update_if_current(contract, expected_version, base_id=data.get("baseId", ""))
            if updated_contract is None:
                contract.refresh_from_db(fields=["version"])
                return version_conflict_response(contract, expected_version)
            contract = updated_contract
        history = ContractHistory.objects.create(
            id=contract_id,
            sellers=", ".join(seller.get("name", "") for seller in data.get("sellers", [])),
            buyer=data.get("buyer", {}).get("name", ""),
            contract_number=str(data.get("contractNumber", "")),
            created_at=timezone.now(),
            data=data,
            cadastres=", ".join(item.get("id", "") for item in data.get("details", {}).get("cadastres", [])),
        )
    return Response({"id": history.id, "version": contract.version, "pdf": f"/api/services/contracts/{history.id}/pdf"}, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
@permission_classes([IsAdmin])
def contract_detail(request, contract_id: str):
    history = get_object_or_404(ContractHistory, id=contract_id)
    contract = get_object_or_404(Contract, id=contract_id)
    if request.method == "DELETE":
        expected_version = requested_version(request)
        if expected_version is None:
            return missing_version_response()
        if not delete_if_current(contract, expected_version):
            contract.refresh_from_db(fields=["version"])
            return version_conflict_response(contract, expected_version)
        history.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    payload = dict(history.data)
    payload["version"] = contract.version
    payload["template"] = contract.template_snapshot or payload.get("template") or None
    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAdmin])
def contract_pdf(request, contract_id: str):
    contract = get_object_or_404(Contract, id=contract_id)
    if contract.document_file:
        return FileResponse(contract.document_file.open("rb"), content_type="application/pdf", as_attachment=True, filename=f"contract-{contract_id}.pdf")
    if not contract.document:
        return _detail("No generated PDF is attached to this contract.", status.HTTP_404_NOT_FOUND)
    return FileResponse(BytesIO(bytes(contract.document)), content_type="application/pdf", as_attachment=True, filename=f"contract-{contract_id}.pdf")


@api_view(["POST"])
@permission_classes([IsAdmin])
def contract_document_upload(request, contract_id: str):
    """Store an uploaded contract under the configured local media directory."""
    uploaded = request.FILES.get("file")
    if uploaded is None:
        return _detail("A file field is required.")
    if uploaded.content_type not in {"application/pdf", "application/x-pdf"}:
        return _detail("Only PDF contract files are accepted.", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    contract = get_object_or_404(Contract, id=contract_id)
    expected_version = requested_version(request)
    if expected_version is None:
        return missing_version_response()
    contract.document_file.save(f"contract-{contract_id}.pdf", uploaded, save=False)
    updated_contract = update_if_current(contract, expected_version, document_file=contract.document_file.name)
    if updated_contract is None:
        contract.document_file.delete(save=False)
        contract.refresh_from_db(fields=["version"])
        return version_conflict_response(contract, expected_version)
    return Response({"id": updated_contract.id, "version": updated_contract.version, "document": updated_contract.document_file.url}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAdmin])
def contract_starter(request):
    return Response({"buyers": [], "templates": [], "statuses": [owner_status_data(item) for item in OwnerStatus.objects.all()]})


@api_view(["GET"])
@permission_classes([IsAdmin])
def contract_cadastre_suggest(request, cadastre_id: str):
    return Response([cadastre_data(item) for item in Cadastre.objects.filter(id__icontains=cadastre_id)[:20]])


@api_view(["GET"])
@permission_classes([IsAdmin])
def contract_owner_suggest(request, owner_id: str):
    return Response([owner_summary(item) for item in Owner.objects.select_related("assignee").filter(id__icontains=owner_id)[:20]])


@api_view(["GET"])
@permission_classes([CanManageOwners])
def owner_followings(request, owner_id: str):
    owner, denied = _owner_or_forbidden(request, owner_id)
    if denied:
        return denied
    follower_ids = list(owner.followings.values_list("user_id", flat=True))
    potential_ids = list(organization_users(request, active_only=True).exclude(id__in=follower_ids).values_list("id", flat=True))
    return Response({"followers": follower_ids, "potentialFollowers": potential_ids})


@api_view(["POST", "DELETE"])
@permission_classes([CanManageOwners])
def owner_following_detail(request, owner_id: str, user_id: str):
    owner, denied = _owner_or_forbidden(request, owner_id)
    if denied:
        return denied
    user = organization_user_or_404(request, user_id)
    if request.method == "POST":
        OwnerFollowing.objects.get_or_create(owner=owner, user=user)
    else:
        OwnerFollowing.objects.filter(owner=owner, user=user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAdmin])
def user_statistics_prep(request):
    return Response({"users": [user_data(user) for user in organization_users(request, active_only=True)], "statuses": list(OwnerStatus.objects.values_list("id", flat=True))})


@extend_schema(
    parameters=[
        OpenApiParameter("from", OpenApiTypes.DATETIME, OpenApiParameter.QUERY, description="Inclusive ISO-8601 start date or datetime."),
        OpenApiParameter("to", OpenApiTypes.DATETIME, OpenApiParameter.QUERY, description="Inclusive ISO-8601 end date or datetime."),
        OpenApiParameter("fromStatus", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by the previous owner status."),
        OpenApiParameter("toStatus", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Filter by the new owner status."),
        OpenApiParameter("granularity", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Aggregation cadence: hour, day, week, or month."),
    ]
)
@api_view(["GET"])
@permission_classes([IsAdmin])
def user_statistics(request):
    """Return tenant-scoped owner-status changes grouped at the requested cadence."""

    granularity = request.query_params.get("granularity", "day").lower()
    truncators = {"hour": TruncHour, "day": TruncDay, "week": TruncWeek, "month": TruncMonth}
    if granularity not in truncators:
        return _detail("granularity must be one of: hour, day, week, month.")
    try:
        from_at = _statistics_boundary(request.query_params.get("from"), parameter="from")
        to_at = _statistics_boundary(request.query_params.get("to"), parameter="to", inclusive_day_end=True)
    except ValueError as exc:
        return _detail(str(exc))
    if from_at and to_at and from_at >= to_at:
        return _detail("from must be before to.")

    changes = OwnerStatusChange.objects.filter(organization_id=request_organization_id(request))
    if from_at:
        changes = changes.filter(timestamp__gte=from_at)
    if to_at:
        changes = changes.filter(timestamp__lt=to_at)
    from_status = request.query_params.get("fromStatus")
    to_status = request.query_params.get("toStatus")
    if from_status:
        changes = changes.filter(from_status=from_status)
    if to_status:
        changes = changes.filter(to_status=to_status)

    frames = changes.annotate(since=truncators[granularity]("timestamp")).values("user_id", "since").annotate(count=Count("id")).order_by("user_id", "since")
    grouped: dict[str, list[dict]] = {}
    for frame in frames:
        grouped.setdefault(frame["user_id"], []).append({"since": json_value(frame["since"]), "count": frame["count"]})
    return Response([{"userId": user_id, "statisticsFrames": values} for user_id, values in grouped.items()])


@api_view(["GET"])
@permission_classes([IsAdmin])
def dashboard_stats(request):
    """Return compact organization-scoped management counts for the dashboard."""

    organization_id = request_organization_id(request)
    now = timezone.now()
    today = timezone.localdate(now)
    upcoming_at = now + timedelta(days=7)
    upcoming_date = today + timedelta(days=7)
    active_owner_scope = Q(out_of_admin_search_from__isnull=True) | Q(out_of_admin_search_to__lte=now)
    owners = Owner.objects.filter(organization_id=organization_id).filter(active_owner_scope)
    deals = Deal.objects.filter(organization_id=organization_id)
    reminders = Reminder.objects.filter(organization_id=organization_id)
    inheritance_cases = InheritanceCase.objects.filter(organization_id=organization_id).exclude(status__in=["COMPLETED", "CLOSED"])

    deal_stage_counts = {stage: 0 for stage, _label in DealStage.choices}
    deal_stage_counts.update({frame["stage"]: frame["count"] for frame in deals.values("stage").annotate(count=Count("id"))})
    reminder_overdue = reminders.filter(due_time__lt=now).count()
    reminder_upcoming = reminders.filter(due_time__gte=now, due_time__lte=upcoming_at).count()
    inheritance_overdue = inheritance_cases.filter(certification_deadline__lt=today).count()
    inheritance_upcoming = inheritance_cases.filter(certification_deadline__gte=today, certification_deadline__lte=upcoming_date).count()
    offer_overdue = deals.exclude(stage__in=[DealStage.WON, DealStage.LOST, DealStage.CANCELLED]).filter(offer_valid_until__lt=today).count()
    offer_upcoming = deals.exclude(stage__in=[DealStage.WON, DealStage.LOST, DealStage.CANCELLED]).filter(offer_valid_until__gte=today, offer_valid_until__lte=upcoming_date).count()

    return Response(
        {
            "activeOwners": owners.count(),
            "newLeads": owners.filter(Q(status="") | Q(status="NEW")).count(),
            "evaluationPending": owners.filter(status="WAITS_FOR_EVALUATION").count(),
            "deadlines": {
                "overdue": reminder_overdue + inheritance_overdue + offer_overdue,
                "nextSevenDays": reminder_upcoming + inheritance_upcoming + offer_upcoming,
                "reminders": {"overdue": reminder_overdue, "nextSevenDays": reminder_upcoming},
                "inheritance": {"overdue": inheritance_overdue, "nextSevenDays": inheritance_upcoming},
                "offers": {"overdue": offer_overdue, "nextSevenDays": offer_upcoming},
            },
            "dealStages": deal_stage_counts,
            "generatedAt": now,
        }
    )


@api_view(["GET"])
@permission_classes([CanManageSales])
def sales_management_overview(request):
    """Return tenant-scoped operational sales workload and intervention signals."""

    organization_id = request_organization_id(request)
    now = timezone.now()
    today = timezone.localdate(now)
    recent_at = now - timedelta(days=30)
    closed_stages = (DealStage.WON, DealStage.LOST, DealStage.CANCELLED)
    team = {
        member.id: {
            "member": user_data(member),
            "workload": {"assignedOwners": 0, "activeDeals": 0, "evaluationDeals": 0, "overdueReminders": 0},
            "contactOutcomes": {outcome: 0 for outcome in ("CALLBACK", "NO_ANSWER", "INTERESTED", "NOT_INTERESTED", "DECLINED", "FOLLOW_UP")},
            "deals": {stage: 0 for stage, _label in DealStage.choices},
        }
        for member in organization_users(request, active_only=True).only("id", "full_name")
    }
    owner_rows = list(Owner.objects.filter(organization_id=organization_id).values("id", "name", "assignee_id"))
    owners_by_id = {str(item["id"]): item for item in owner_rows}
    active_owner_scope = Q(out_of_admin_search_from__isnull=True) | Q(out_of_admin_search_to__lte=now)
    for frame in Owner.objects.filter(organization_id=organization_id).filter(active_owner_scope).values("assignee_id").annotate(count=Count("id")):
        if frame["assignee_id"] in team:
            team[frame["assignee_id"]]["workload"]["assignedOwners"] = frame["count"]

    interventions = []
    deals = Deal.objects.filter(organization_id=organization_id)
    for deal in deals.values("id", "owner_id", "owner__assignee_id", "evaluator_id", "stage", "offer_valid_until"):
        assignee_id = deal["owner__assignee_id"]
        if assignee_id in team:
            team[assignee_id]["deals"][deal["stage"]] += 1
            if deal["stage"] not in closed_stages:
                team[assignee_id]["workload"]["activeDeals"] += 1
        if deal["stage"] == DealStage.EVALUATION and deal["evaluator_id"] in team:
            team[deal["evaluator_id"]]["workload"]["evaluationDeals"] += 1
        owner = owners_by_id.get(str(deal["owner_id"]))
        if deal["stage"] == DealStage.EVALUATION and not deal["evaluator_id"] and owner:
            interventions.append({"kind": "UNASSIGNED_EVALUATION", "dealId": str(deal["id"]), "ownerId": str(deal["owner_id"]), "ownerName": owner["name"], "assigneeId": assignee_id, "dueAt": None})
        if deal["stage"] not in closed_stages and deal["offer_valid_until"] and deal["offer_valid_until"] < today and owner:
            interventions.append({"kind": "EXPIRED_OFFER", "dealId": str(deal["id"]), "ownerId": str(deal["owner_id"]), "ownerName": owner["name"], "assigneeId": assignee_id, "dueAt": deal["offer_valid_until"].isoformat()})

    for reminder in Reminder.objects.filter(organization_id=organization_id, due_time__lt=now).values("id", "owner_id", "due_time"):
        owner = owners_by_id.get(str(reminder["owner_id"]))
        if owner and owner["assignee_id"] in team:
            team[owner["assignee_id"]]["workload"]["overdueReminders"] += 1
        if owner:
            interventions.append({"kind": "OVERDUE_REMINDER", "reminderId": str(reminder["id"]), "ownerId": str(reminder["owner_id"]), "ownerName": owner["name"], "assigneeId": owner["assignee_id"], "dueAt": reminder["due_time"].isoformat()})

    for contact in OwnerLog.objects.filter(organization_id=organization_id, created_at__gte=recent_at, message__startswith="Sales outcome:").values("creator_id", "message"):
        if contact["creator_id"] not in team:
            continue
        outcome = contact["message"].split(" ", 2)[2].split(".", 1)[0]
        if outcome in team[contact["creator_id"]]["contactOutcomes"]:
            team[contact["creator_id"]]["contactOutcomes"][outcome] += 1

    return Response(
        {
            "period": {"contactOutcomesSince": json_value(recent_at), "generatedAt": json_value(now)},
            "team": list(team.values()),
            "interventions": sorted(interventions, key=lambda item: (item["dueAt"] is None, item["dueAt"] or "", item["kind"]))[:100],
        }
    )
