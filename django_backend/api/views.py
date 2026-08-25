"""ForestIQ REST endpoints implemented with Django ORM and PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timedelta
from io import BytesIO
import json
from uuid import uuid4

from django.db import transaction
from django.db.models import Count, Q
from django.contrib.gis.geos import Polygon
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
from operations.models import ApplicationMessage, Contract, ContractHistory, DirectMessage, PersonDump, Reminder

from .permissions import CanEvaluate, CanManageOwners, CanUseAssignedOwners, CanUsePhones, IsAdmin, can_access_owner
from .serializers import (
    cadastre_data,
    json_value,
    message_data,
    notification_data,
    owner_data,
    owner_log_data,
    owner_status_data,
    owner_summary,
    reminder_data,
    user_data,
)
from forestry.tasks import enqueue_cadastre_sync


def _detail(message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> Response:
    return Response({"detail": message}, status=http_status)


def _sync_run_data(run: DataSyncRun) -> dict:
    return {
        "id": run.id,
        "cadastre": run.cadastre_id,
        "taskId": run.task_id,
        "source": run.source,
        "status": run.status,
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
    run = enqueue_cadastre_sync(cadastre.id, requested_by_id=request.user.id, source="api")
    return Response(_sync_run_data(run), status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cadastre_map_features(request):
    """Return validated cadastral geometries as WGS84 GeoJSON for MapLibre."""
    cadastres = Cadastre.objects.exclude(boundary__isnull=True)
    raw_bbox = request.query_params.get("bbox", "").strip()
    if raw_bbox:
        try:
            west, south, east, north = (float(value) for value in raw_bbox.split(","))
            if west >= east or south >= north:
                raise ValueError
            viewport = Polygon.from_bbox((west, south, east, north))
            viewport.srid = 4326
            viewport.transform(3301)
            cadastres = cadastres.filter(boundary__intersects=viewport)
        except ValueError:
            return _detail("bbox must contain west,south,east,north in EPSG:4326")
    features = []
    for cadastre in cadastres.order_by("id")[:1000]:
        geometry = cadastre.boundary.clone()
        geometry.transform(4326)
        features.append({"type": "Feature", "id": cadastre.id, "geometry": json.loads(geometry.json), "properties": {"id": cadastre.id, "name": cadastre.name, "county": cadastre.county, "area": str(cadastre.area or "")}})
    return Response({"type": "FeatureCollection", "features": features})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def map_layer_features(request, layer: str):
    """Return validated GeoDjango layers as WGS84 GeoJSON for the MapLibre client."""

    layer = layer.lower()
    if layer not in {"subparts", "registry", "notifications"}:
        return _detail("Unknown map layer.", status.HTTP_404_NOT_FOUND)
    features = []
    if layer == "subparts":
        records = CadastreSubPart.objects.exclude(boundary__isnull=True).select_related("cadastre").order_by("cadastre_id", "sub_part_code")[:5000]
        for record in records:
            geometry = record.boundary.clone()
            geometry.transform(4326)
            features.append({"type": "Feature", "id": f"{record.cadastre_id}:{record.sub_part_code}", "geometry": json.loads(geometry.json), "properties": {"id": f"{record.cadastre_id}:{record.sub_part_code}", "cadastreId": record.cadastre_id, "subpartCode": record.sub_part_code, "treeType": record.tree_type_code, "area": str(record.area or "")}})
    elif layer == "registry":
        records = ForestRegistryFeature.objects.exclude(spatial_geometry__isnull=True).select_related("cadastre").order_by("cadastre_id", "source_layer", "source_id")[:5000]
        for record in records:
            geometry = record.spatial_geometry.clone()
            geometry.transform(4326)
            features.append({"type": "Feature", "id": f"{record.source_layer}:{record.source_id}", "geometry": json.loads(geometry.json), "properties": {"id": f"{record.source_layer}:{record.source_id}", "cadastreId": record.cadastre_id, "subpartCode": record.subpart_code, "title": record.title, "workCode": record.work_code, "decision": record.decision, "area": str(record.area or "")}})
    else:
        records = CadastreNotification.objects.exclude(cadastre_subpart_code__isnull=True).select_related("cadastre").order_by("-registration_date", "-id")[:5000]
        for record in records:
            subpart = CadastreSubPart.objects.filter(cadastre_id=record.cadastre_id, sub_part_code=record.cadastre_subpart_code).exclude(boundary__isnull=True).first()
            if not subpart:
                continue
            geometry = subpart.boundary.centroid
            geometry.transform(4326)
            features.append({"type": "Feature", "id": str(record.id), "geometry": json.loads(geometry.json), "properties": {"id": str(record.id), "cadastreId": record.cadastre_id, "subpartCode": record.cadastre_subpart_code, "notificationNumber": record.notification_number, "workCode": record.work_code, "state": record.state, "registrationDate": record.registration_date.isoformat() if record.registration_date else ""}})
    return Response({"type": "FeatureCollection", "features": features})


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
    if not can_access_owner(request.user, owner):
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
    if not request.user.has_privilege(PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
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
@permission_classes([IsAuthenticated])
def service_status(request):
    return Response({"status": "OK", "service": "forestiq-django", "time": int(timezone.now().timestamp() * 1000)})


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def admin_users(request):
    if request.method == "GET":
        return Response([_user_payload(user) for user in User.objects.prefetch_related("privilege_assignments").all()])

    user_id = str(request.data.get("id", "")).strip()
    full_name = str(request.data.get("name", "")).strip()
    password = request.data.get("password")
    privileges = request.data.get("privileges", [])
    if not user_id or not full_name or not password:
        return _detail("id, name and password are required.")
    if User.objects.filter(id=user_id).exists():
        return _detail("A user with that id already exists.", status.HTTP_409_CONFLICT)
    with transaction.atomic():
        user = User.objects.create_user(user_id, full_name, password)
        Privilege.objects.bulk_create([Privilege(user=user, code=code) for code in privileges if code in PrivilegeCode.values])
        sync_user_groups(user)
    return Response(_user_payload(user), status=status.HTTP_201_CREATED)


@api_view(["POST", "DELETE"])
@permission_classes([IsAdmin])
def admin_user_detail(request, user_id: str):
    user = get_object_or_404(User, id=user_id)
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
    for field in editable:
        if field in request.data:
            setattr(owner, field, request.data[field] or "")
    owner.save(update_fields=[field for field in editable if field in request.data])
    return Response(owner_data(owner))


@api_view(["POST"])
@permission_classes([CanManageOwners])
def owner_add(request, owner_id: str):
    if not request.user.has_privilege(PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
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
                "possibleAssignees": [user_data(user) for user in User.objects.filter(is_active=True)],
                "possibleOwnerStatuses": list(OwnerStatus.objects.values_list("id", flat=True)),
                "status": owner.status,
                "assignee": user_data(owner.assignee),
            }
        )
    new_status = str(request.data.get("code", "")).strip()
    if not OwnerStatus.objects.filter(id=new_status).exists():
        return _detail("Unknown owner status.")
    old_status = owner.status
    owner.status = new_status
    owner.status_set_at = timezone.now()
    owner.save(update_fields=["status", "status_set_at"])
    OwnerStatusChange.objects.create(user=request.user, from_status=old_status, to_status=new_status)
    return Response(owner_data(owner))


@api_view(["POST"])
@permission_classes([IsAdmin])
def owner_assignee(request, owner_id: str):
    owner = get_object_or_404(Owner, id=owner_id)
    assignee_id = request.data.get("assignee")
    assignee = get_object_or_404(User, id=assignee_id) if assignee_id else None
    owner.assignee = assignee
    owner.save(update_fields=["assignee"])
    return Response(owner_data(owner))


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
    if not any(can_access_owner(request.user, owner) for owner in owners):
        return _detail("You do not have access to this cadastre.", status.HTTP_403_FORBIDDEN)
    return Response(cadastre_data(cadastre))


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
            "users": [user_data(user) for user in User.objects.filter(is_active=True)],
        }
    )


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_workdesk_prep(request):
    return Response(
        {
            "statuses": [owner_status_data(item) for item in OwnerStatus.objects.all()],
            "users": [user_data(user) for user in User.objects.filter(is_active=True)],
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
    assignee = get_object_or_404(User, id=request.data.get("userId"))
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
    if reminder.creator_id != request.user.id and (not reminder.owner or reminder.owner.assignee_id != request.user.id) and not request.user.has_privilege(PrivilegeCode.ADMIN):
        return _detail("You do not have access to this reminder.", status.HTTP_403_FORBIDDEN)
    reminder.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reminders_dashboard(request):
    records = Reminder.objects.select_related("owner", "owner__assignee", "creator").filter(due_time__lte=timezone.now() + timedelta(days=7))
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
@permission_classes([IsAuthenticated])
def received_messages(request):
    records = DirectMessage.objects.select_related("sender", "recipient").filter(recipient=request.user)
    return Response([message_data(item) for item in _paginate(records, request)])


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sent_messages(request):
    records = DirectMessage.objects.select_related("sender", "recipient").filter(sender=request.user)
    return Response([message_data(item) for item in _paginate(records, request)])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request):
    recipient = get_object_or_404(User, id=request.data.get("recipient"))
    text = str(request.data.get("message", "")).strip()
    if not text:
        return _detail("Message is required.")
    message = DirectMessage.objects.create(sender=request.user, recipient=recipient, text=text)
    return Response(message_data(message), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def message_users(request):
    return Response(list(User.objects.filter(is_active=True).values_list("id", flat=True)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def new_messages_count(request):
    return Response({"newMessageCount": DirectMessage.objects.filter(recipient=request.user, noticed_at__isnull=True).count()})


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def contracts(request):
    if request.method == "GET":
        return Response(
            [
                {"id": item.id, "sellers": item.sellers, "buyer": item.buyer, "contractNo": item.contract_number, "created": json_value(item.created_at)}
                for item in ContractHistory.objects.all()
            ]
        )
    data = request.data
    contract_id = str(data.get("id") or uuid4())
    history = ContractHistory.objects.create(
        id=contract_id,
        sellers=", ".join(seller.get("name", "") for seller in data.get("sellers", [])),
        buyer=data.get("buyer", {}).get("name", ""),
        contract_number=str(data.get("contractNumber", "")),
        created_at=timezone.now(),
        data=data,
        cadastres=", ".join(item.get("id", "") for item in data.get("details", {}).get("cadastres", [])),
    )
    Contract.objects.update_or_create(id=contract_id, defaults={"base_id": data.get("baseId", "")})
    return Response({"id": history.id, "pdf": f"/api/services/contracts/{history.id}/pdf"}, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
@permission_classes([IsAdmin])
def contract_detail(request, contract_id: str):
    history = get_object_or_404(ContractHistory, id=contract_id)
    if request.method == "DELETE":
        Contract.objects.filter(id=contract_id).delete()
        history.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(history.data)


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
    contract.document_file.save(f"contract-{contract_id}.pdf", uploaded, save=True)
    return Response({"id": contract.id, "document": contract.document_file.url}, status=status.HTTP_201_CREATED)


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
    potential_ids = list(User.objects.exclude(id__in=follower_ids).filter(is_active=True).values_list("id", flat=True))
    return Response({"followers": follower_ids, "potentialFollowers": potential_ids})


@api_view(["POST", "DELETE"])
@permission_classes([CanManageOwners])
def owner_following_detail(request, owner_id: str, user_id: str):
    owner, denied = _owner_or_forbidden(request, owner_id)
    if denied:
        return denied
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        OwnerFollowing.objects.get_or_create(owner=owner, user=user)
    else:
        OwnerFollowing.objects.filter(owner=owner, user=user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAdmin])
def user_statistics_prep(request):
    return Response({"users": [user_data(user) for user in User.objects.filter(is_active=True)], "statuses": list(OwnerStatus.objects.values_list("id", flat=True))})


@api_view(["GET"])
@permission_classes([IsAdmin])
def user_statistics(request):
    frames = (
        OwnerStatusChange.objects.values("user_id")
        .annotate(count=Count("id"))
        .order_by("user_id")
    )
    return Response([{"userId": frame["user_id"], "statisticsFrames": [{"since": None, "count": frame["count"]}]} for frame in frames])
