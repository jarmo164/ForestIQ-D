"""P1 operational APIs: structured work, deal health, contracts, quality and ownership."""
from __future__ import annotations

import base64
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from urllib.parse import urlparse

from django.conf import settings
from django.db import transaction
from django.db.models import Count, DecimalField, Max, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import PrivilegeCode
from accounts.models import User
from forestry.models import Cadastre, CadastreNotification, ForestRegistryFeature, Owner, OwnerCadastre, OwnerLog
from operations.models import Contract, ContractHistory, Deal, DealOffer, DealStage, OwnershipTransitionEvent
from operations.p1_models import (
    ContactActivity,
    ContractSigning,
    ContractSigningEvent,
    ContractVersion,
    DataQualityIssue,
    DataQualityIssueEvent,
    DecisionEvidenceSnapshot,
    DealLossOutcome,
    DealWorkState,
    LossReasonCode,
    MapWorkbasket,
    MapWorkbasketItem,
    NextAction,
    OwnershipRelation,
    OwnershipRelationEvent,
    SalesSegment,
    SalesStageProbability,
    WorkflowAuditEvent,
)
from operations.services.contract_pdf import ContractPdfRenderError, render_contract_pdf
from operations.services.signature_verification import SignatureVerificationError, file_sha256, stored_file_integrity, verify_provider_evidence
from operations.realtime import publish_org_event

from .concurrency import requested_version, version_conflict_response
from .contract_templates import render_template_preview_html
from .organization import organization_user_or_404, request_organization_id
from .parity import _commercial, _get_deal, _update_deal_or_conflict
from .permissions import CanManageOwners, CanManageSales, IsAdmin, can_access_deal, can_access_owner, current_membership, has_membership_privilege
from .serializers import json_value, owner_summary, user_data


CLOSED_DEAL_STAGES = (DealStage.WON, DealStage.LOST, DealStage.CANCELLED)
DEFAULT_LOSS_REASONS = (
    ("PRICE", "Price", 10),
    ("NO_INTEREST", "No interest", 20),
    ("COMPETITOR", "Competitor", 30),
    ("TIMING", "Timing", 40),
    ("OTHER", "Other", 100),
)
SIGNING_TRANSITIONS = {
    ContractSigning.State.PREPARING: {ContractSigning.State.SENT_FOR_SIGNATURE, ContractSigning.State.CANCELLED},
    ContractSigning.State.SENT_FOR_SIGNATURE: {ContractSigning.State.SIGNED, ContractSigning.State.CANCELLED},
    ContractSigning.State.SIGNED: set(),
    ContractSigning.State.CANCELLED: set(),
}
CONTRACT_CHECKLIST = ("priceMatched", "termsMatched", "sellerMatched", "parcelsMatched")
DECISION_EVIDENCE_SCHEMA_VERSION = 1
SALES_STAGE_ORDER = (DealStage.QUALIFICATION, DealStage.EVALUATION, DealStage.NEGOTIATION, DealStage.WON, DealStage.LOST, DealStage.CANCELLED)
SALES_DEFAULT_PROBABILITIES = {
    DealStage.QUALIFICATION: Decimal("0.1500"),
    DealStage.EVALUATION: Decimal("0.3500"),
    DealStage.NEGOTIATION: Decimal("0.6500"),
    DealStage.WON: Decimal("1.0000"),
    DealStage.LOST: Decimal("0.0000"),
    DealStage.CANCELLED: Decimal("0.0000"),
}


def _detail(message: str, http_status: int = status.HTTP_400_BAD_REQUEST) -> Response:
    return Response({"detail": message}, status=http_status)


def _parse_datetime(value, field: str = "datetime"):
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value) / 1000, tz=timezone.get_current_timezone())
        except (OverflowError, OSError, ValueError) as exc:
            raise ValueError(f"{field} is invalid.") from exc
    parsed = parse_datetime(str(value).replace("Z", "+00:00"))
    if parsed is None:
        raise ValueError(f"{field} must be an ISO datetime or epoch milliseconds.")
    return timezone.make_aware(parsed, timezone.get_current_timezone()) if timezone.is_naive(parsed) else parsed


def _parse_date(value, field: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD.") from exc


def _encode_cursor(value: str) -> str:
    raw = json.dumps({"id": value}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_cursor(value: str | None) -> str | None:
    if not value:
        return None
    try:
        padded = value + "=" * (-len(value) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
        cursor_id = str(payload["id"])
        if not cursor_id:
            raise ValueError
        return cursor_id
    except (KeyError, ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("cursor is invalid or expired.") from exc


def _limit(request, default: int = 50, maximum: int = 100) -> int:
    try:
        return min(max(int(request.query_params.get("limit", default)), 1), maximum)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"limit must be between 1 and {maximum}.") from exc


def _owner_or_403(request, owner_id: str):
    owner = get_object_or_404(Owner.objects.select_related("assignee"), id=owner_id)
    if not can_access_owner(request, owner):
        return None, _detail("You do not have access to this owner.", status.HTTP_403_FORBIDDEN)
    return owner, None


def _deal_or_403(request, deal_id: str):
    deal = _get_deal(deal_id)
    if not can_access_deal(request, deal):
        return None, _detail("You do not have access to this deal.", status.HTTP_403_FORBIDDEN)
    return deal, None


def _audit(*, owner=None, deal=None, activity=None, next_action=None, actor=None, event_type: str, payload=None):
    event = WorkflowAuditEvent.objects.create(
        owner=owner,
        deal=deal,
        activity=activity,
        next_action=next_action,
        actor=actor,
        event_type=event_type,
        payload=payload or {},
    )
    publish_org_event(
        "WORKFLOW_EVENT",
        {
            "workflowEventId": event.pk,
            "type": event_type,
            "ownerId": getattr(owner, "id", None),
            "dealId": str(getattr(deal, "id", "")) or None,
            "payload": payload or {},
        },
        actor=actor,
    )
    return event


def _action_data(action: NextAction | None):
    if action is None:
        return None
    return {
        "id": str(action.id),
        "ownerId": action.owner_id,
        "dealId": str(action.deal_id) if action.deal_id else None,
        "text": action.text,
        "dueAt": json_value(action.due_at),
        "assignee": user_data(action.assignee),
        "status": action.status,
        "completedAt": json_value(action.completed_at),
        "createdAt": json_value(action.created_at),
        "updatedAt": json_value(action.updated_at),
    }


def _activity_data(activity: ContactActivity):
    return {
        "id": str(activity.id),
        "ownerId": activity.owner_id,
        "dealId": str(activity.deal_id) if activity.deal_id else None,
        "channel": activity.channel,
        "outcomeCode": activity.outcome_code,
        "outcomeReason": activity.outcome_reason or None,
        "note": activity.note or None,
        "createdBy": user_data(activity.created_by),
        "createdAt": json_value(activity.created_at),
        "nextActions": [_action_data(item) for item in activity.next_actions.select_related("assignee").all()],
    }


def _event_data(event: WorkflowAuditEvent):
    return {
        "id": str(event.id),
        "type": event.event_type,
        "ownerId": event.owner_id,
        "dealId": str(event.deal_id) if event.deal_id else None,
        "activityId": str(event.activity_id) if event.activity_id else None,
        "nextActionId": str(event.next_action_id) if event.next_action_id else None,
        "actor": user_data(event.actor),
        "payload": event.payload,
        "createdAt": json_value(event.created_at),
    }


def _owner_relation_counts(owner: Owner) -> dict:
    _project_legacy_relations(owner)
    counts = OwnershipRelation.objects.filter(owner=owner).aggregate(
        active=Count("id", filter=Q(is_active=True)),
        historical=Count("id", filter=Q(is_active=False)),
    )
    return {"active": counts["active"] or 0, "historical": counts["historical"] or 0}


def _owner_map_feature(relation: OwnershipRelation) -> dict:
    cadastre = relation.cadastre
    geometry = None
    if cadastre.boundary:
        boundary = cadastre.boundary.clone()
        boundary.transform(4326)
        geometry = json.loads(boundary.geojson)
    properties = {
        "cadastreId": cadastre.id,
        "name": cadastre.name or None,
        "area": json_value(cadastre.area),
        "forestArea": json_value(cadastre.forest_area),
        "county": cadastre.county or None,
        "municipality": cadastre.municipality or None,
        "active": relation.is_active,
        "relationId": str(relation.id),
        "source": relation.source,
        "validFrom": json_value(relation.valid_from),
        "validTo": json_value(relation.valid_to),
    }
    return {"type": "Feature", "id": str(relation.id), "geometry": geometry, "properties": properties}


def _owner_360_timeline_item(kind: str, source: str, record_id: str, occurred_at, title: str, description: str = "", target: dict | None = None, actor=None, payload: dict | None = None) -> dict:
    return {
        "id": f"{source}:{record_id}",
        "type": kind,
        "source": source,
        "occurredAt": json_value(occurred_at),
        "title": title,
        "description": description or "",
        "target": target or {},
        "actor": user_data(actor),
        "payload": payload or {},
    }


def _request_role_codes(request) -> set[str]:
    membership = current_membership(request)
    return set(getattr(membership, "role_codes", []) or [])


def _workbasket_access_q(request):
    role_codes = _request_role_codes(request)
    query = Q(created_by=request.user) | Q(assigned_to_user=request.user)
    if role_codes:
        query |= Q(assigned_to_role__in=role_codes)
    return query


def _can_view_workbasket(request, basket: MapWorkbasket) -> bool:
    return bool(
        has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE)
        or basket.created_by_id == request.user.id
        or basket.assigned_to_user_id == request.user.id
        or (basket.assigned_to_role and basket.assigned_to_role in _request_role_codes(request))
    )


def _can_edit_workbasket(request, basket: MapWorkbasket) -> bool:
    if basket.status == MapWorkbasket.Status.CANCELLED:
        return False
    if basket.created_by_id == request.user.id:
        return True
    if basket.permission != MapWorkbasket.Permission.EDIT:
        return False
    return bool(
        basket.assigned_to_user_id == request.user.id
        or (basket.assigned_to_role and basket.assigned_to_role in _request_role_codes(request))
    )


def _workbasket_or_403(request, basket_id: str):
    basket = get_object_or_404(
        MapWorkbasket.objects.select_related("created_by", "assigned_to_user", "accepted_by").prefetch_related("items__cadastre", "items__added_by"),
        id=basket_id,
    )
    if not _can_view_workbasket(request, basket):
        return None, _detail("You do not have access to this map workbasket.", status.HTTP_403_FORBIDDEN)
    return basket, None


def _cadastre_item_data(item: MapWorkbasketItem):
    cadastre = item.cadastre
    return {
        "id": str(item.id),
        "cadastre": {
            "id": cadastre.id,
            "name": cadastre.name or None,
            "county": cadastre.county or None,
            "municipality": cadastre.municipality or None,
            "address": cadastre.address or None,
            "area": json_value(cadastre.area),
            "forestArea": json_value(cadastre.forest_area),
            "mkDate": json_value(cadastre.mk_date),
        },
        "addedBy": user_data(item.added_by),
        "addedAt": json_value(item.added_at),
        "sortOrder": item.sort_order,
    }


def _workbasket_payload(request, basket: MapWorkbasket, *, include_items: bool = True):
    items = list(basket.items.select_related("cadastre", "added_by").all()) if include_items else []
    return {
        "id": str(basket.id),
        "name": basket.name,
        "description": basket.description or None,
        "purpose": basket.purpose or None,
        "dueAt": json_value(basket.due_at),
        "permission": basket.permission,
        "status": basket.status,
        "createdBy": user_data(basket.created_by),
        "assignedToUser": user_data(basket.assigned_to_user),
        "assignedToRole": basket.assigned_to_role or None,
        "acceptedBy": user_data(basket.accepted_by),
        "acceptedAt": json_value(basket.accepted_at),
        "cancelledAt": json_value(basket.cancelled_at),
        "createdAt": json_value(basket.created_at),
        "updatedAt": json_value(basket.updated_at),
        "cadastreCount": len(items) if include_items else basket.items.count(),
        "editable": _can_edit_workbasket(request, basket),
        "items": [_cadastre_item_data(item) for item in items] if include_items else None,
    }


def _replace_workbasket_items(basket: MapWorkbasket, cadastre_ids: list[str], actor) -> None:
    if len(cadastre_ids) > 250:
        raise ValueError("cadastreIds may contain at most 250 entries.")
    ordered_ids = []
    seen = set()
    for cadastre_id in cadastre_ids:
        value = str(cadastre_id).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered_ids.append(value)
    cadastres = {item.id: item for item in Cadastre.objects.filter(id__in=ordered_ids)}
    missing = [item for item in ordered_ids if item not in cadastres]
    if missing:
        raise ValueError(f"Cadastre is not accessible: {missing[0]}.")
    MapWorkbasketItem.objects.filter(basket=basket).delete()
    for index, cadastre_id in enumerate(ordered_ids):
        MapWorkbasketItem.objects.create(basket=basket, cadastre=cadastres[cadastre_id], added_by=actor, sort_order=index)


@api_view(["GET", "POST"])
@permission_classes([CanManageOwners])
def map_workbaskets(request):
    if request.method == "GET":
        queryset = MapWorkbasket.objects.filter(_workbasket_access_q(request)).select_related("created_by", "assigned_to_user", "accepted_by").prefetch_related("items")
        status_filter = str(request.query_params.get("status", "")).strip().upper()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return Response([_workbasket_payload(request, basket, include_items=False) for basket in queryset[:200]])

    name = str(request.data.get("name", "")).strip()
    if not name:
        return _detail("name is required.")
    cadastre_ids = request.data.get("cadastreIds") or []
    if not isinstance(cadastre_ids, list) or not cadastre_ids:
        return _detail("cadastreIds must be a non-empty list.")
    try:
        due_at = _parse_datetime(request.data.get("dueAt"), "dueAt")
        with transaction.atomic():
            basket = MapWorkbasket.objects.create(
                name=name[:160],
                description=str(request.data.get("description", "")).strip(),
                purpose=str(request.data.get("purpose", "")).strip(),
                due_at=due_at,
                created_by=request.user,
            )
            _replace_workbasket_items(basket, cadastre_ids, request.user)
            _audit(actor=request.user, event_type="MAP_WORKBASKET_CREATED", payload={"workbasketId": str(basket.id), "cadastreIds": cadastre_ids})
    except ValueError as exc:
        return _detail(str(exc))
    return Response(_workbasket_payload(request, basket), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([CanManageOwners])
def map_workbasket_detail(request, basket_id: str):
    basket, denied = _workbasket_or_403(request, basket_id)
    if denied:
        return denied
    if request.method == "GET":
        return Response(_workbasket_payload(request, basket))
    if not _can_edit_workbasket(request, basket):
        return _detail("This map workbasket is view-only for you.", status.HTTP_403_FORBIDDEN)
    try:
        with transaction.atomic():
            changed_fields = []
            if "name" in request.data:
                name = str(request.data.get("name", "")).strip()
                if not name:
                    return _detail("name cannot be blank.")
                basket.name = name[:160]
                changed_fields.append("name")
            if "description" in request.data:
                basket.description = str(request.data.get("description", "")).strip()
                changed_fields.append("description")
            if "purpose" in request.data:
                basket.purpose = str(request.data.get("purpose", "")).strip()
                changed_fields.append("purpose")
            if "cadastreIds" in request.data:
                cadastre_ids = request.data.get("cadastreIds")
                if not isinstance(cadastre_ids, list):
                    return _detail("cadastreIds must be a list.")
                _replace_workbasket_items(basket, cadastre_ids, request.user)
                changed_fields.append("cadastreIds")
            if changed_fields:
                basket.save(update_fields=("name", "description", "purpose", "updated_at"))
                _audit(actor=request.user, event_type="MAP_WORKBASKET_UPDATED", payload={"workbasketId": str(basket.id), "fields": changed_fields})
    except ValueError as exc:
        return _detail(str(exc))
    basket.refresh_from_db()
    return Response(_workbasket_payload(request, basket))


@api_view(["POST"])
@permission_classes([CanManageOwners])
def map_workbasket_transfer(request, basket_id: str):
    basket, denied = _workbasket_or_403(request, basket_id)
    if denied:
        return denied
    if basket.created_by_id != request.user.id and not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        return _detail("Only the creator or manager can transfer this map workbasket.", status.HTTP_403_FORBIDDEN)
    if basket.status == MapWorkbasket.Status.ACCEPTED:
        return _detail("Accepted map workbaskets cannot be transferred again.", status.HTTP_409_CONFLICT)
    permission = str(request.data.get("permission", MapWorkbasket.Permission.VIEW)).upper()
    if permission not in MapWorkbasket.Permission.values:
        return _detail("permission must be VIEW or EDIT.")
    assigned_user = None
    assigned_user_id = str(request.data.get("assignedToUserId") or "").strip()
    assigned_role = str(request.data.get("assignedToRole") or "").strip().upper()
    if bool(assigned_user_id) == bool(assigned_role):
        return _detail("Provide exactly one of assignedToUserId or assignedToRole.")
    if assigned_user_id:
        assigned_user = get_object_or_404(User, id=assigned_user_id)
        if not assigned_user.organizations.filter(id=request_organization_id(request)).exists():
            return _detail("Cannot transfer a map workbasket across organizations.", status.HTTP_403_FORBIDDEN)
    try:
        due_at = _parse_datetime(request.data.get("dueAt"), "dueAt")
    except ValueError as exc:
        return _detail(str(exc))
    basket.assigned_to_user = assigned_user
    basket.assigned_to_role = assigned_role
    basket.permission = permission
    basket.purpose = str(request.data.get("purpose", "")).strip()
    basket.due_at = due_at
    basket.status = MapWorkbasket.Status.PENDING
    basket.accepted_by = None
    basket.accepted_at = None
    basket.cancelled_at = None
    basket.save(update_fields=("assigned_to_user", "assigned_to_role", "permission", "purpose", "due_at", "status", "accepted_by", "accepted_at", "cancelled_at", "updated_at"))
    _audit(
        actor=request.user,
        event_type="MAP_WORKBASKET_TRANSFERRED",
        payload={"workbasketId": str(basket.id), "assignedToUserId": assigned_user_id or None, "assignedToRole": assigned_role or None, "permission": permission},
    )
    return Response(_workbasket_payload(request, basket))


@api_view(["POST"])
@permission_classes([CanManageOwners])
def map_workbasket_accept(request, basket_id: str):
    basket, denied = _workbasket_or_403(request, basket_id)
    if denied:
        return denied
    if basket.status != MapWorkbasket.Status.PENDING:
        return _detail("Only pending map workbaskets can be accepted.", status.HTTP_409_CONFLICT)
    if basket.created_by_id == request.user.id and not (basket.assigned_to_user_id == request.user.id or basket.assigned_to_role in _request_role_codes(request)):
        return _detail("The creator cannot accept an unassigned transfer.", status.HTTP_403_FORBIDDEN)
    if not (basket.assigned_to_user_id == request.user.id or basket.assigned_to_role in _request_role_codes(request)):
        return _detail("Only the assigned recipient can accept this map workbasket.", status.HTTP_403_FORBIDDEN)
    basket.status = MapWorkbasket.Status.ACCEPTED
    basket.accepted_by = request.user
    basket.accepted_at = timezone.now()
    basket.save(update_fields=("status", "accepted_by", "accepted_at", "updated_at"))
    _audit(actor=request.user, event_type="MAP_WORKBASKET_ACCEPTED", payload={"workbasketId": str(basket.id)})
    return Response(_workbasket_payload(request, basket))


@api_view(["POST"])
@permission_classes([CanManageOwners])
def map_workbasket_cancel(request, basket_id: str):
    basket, denied = _workbasket_or_403(request, basket_id)
    if denied:
        return denied
    if basket.created_by_id != request.user.id and not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        return _detail("Only the creator or manager can cancel this map workbasket transfer.", status.HTTP_403_FORBIDDEN)
    if basket.status != MapWorkbasket.Status.PENDING:
        return _detail("Only pending map workbasket transfers can be cancelled.", status.HTTP_409_CONFLICT)
    basket.status = MapWorkbasket.Status.CANCELLED
    basket.cancelled_at = timezone.now()
    basket.save(update_fields=("status", "cancelled_at", "updated_at"))
    _audit(actor=request.user, event_type="MAP_WORKBASKET_CANCELLED", payload={"workbasketId": str(basket.id)})
    return Response(_workbasket_payload(request, basket))


def _sales_probability_data(item: SalesStageProbability):
    return {
        "id": str(item.id),
        "stage": item.stage,
        "probability": json_value(item.probability),
        "validFrom": item.valid_from.isoformat(),
        "validTo": item.valid_to.isoformat() if item.valid_to else None,
        "note": item.note or None,
        "createdBy": user_data(item.created_by),
        "createdAt": json_value(item.created_at),
        "updatedAt": json_value(item.updated_at),
    }


def _segment_data(item: SalesSegment):
    return {
        "id": str(item.id),
        "name": item.name,
        "filters": item.filters,
        "shared": item.is_shared,
        "createdBy": user_data(item.created_by),
        "createdAt": json_value(item.created_at),
        "updatedAt": json_value(item.updated_at),
    }


def _sales_base_queryset(request):
    queryset = Deal.objects.select_related("owner", "owner__assignee", "evaluator", "created_by").prefetch_related("offers")
    if not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        queryset = queryset.filter(Q(owner__assignee=request.user) | Q(evaluator=request.user) | Q(created_by=request.user)).distinct()
    return queryset


def _deal_value_basis(deal: Deal) -> tuple[Decimal, str]:
    accepted = next((offer for offer in deal.offers.all() if offer.status == DealOffer.Status.ACCEPTED), None)
    if accepted:
        return accepted.amount, "acceptedOffer"
    for value, source in (
        (deal.proposed_offer_price, "proposedOfferPrice"),
        (deal.recommended_purchase_price, "recommendedPurchasePrice"),
        (deal.price_expectation, "priceExpectation"),
    ):
        if value is not None:
            return value, source
    return Decimal("0.00"), "missing"


def _active_probability_lookup(as_of: date) -> dict[str, tuple[Decimal, SalesStageProbability | None]]:
    probabilities: dict[str, tuple[Decimal, SalesStageProbability | None]] = {stage: (value, None) for stage, value in SALES_DEFAULT_PROBABILITIES.items()}
    configured = SalesStageProbability.objects.filter(valid_from__lte=as_of).filter(Q(valid_to__isnull=True) | Q(valid_to__gte=as_of)).order_by("stage", "-valid_from", "-created_at")
    seen = set()
    for item in configured:
        if item.stage in seen:
            continue
        seen.add(item.stage)
        probabilities[item.stage] = (item.probability, item)
    return probabilities


def _median_decimal(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / Decimal("2")


def _segment_queryset(request, filters: dict):
    queryset = _sales_base_queryset(request)
    stages = filters.get("stages") if isinstance(filters.get("stages"), list) else []
    valid_stages = [str(stage).upper() for stage in stages if str(stage).upper() in DealStage.values]
    if valid_stages:
        queryset = queryset.filter(stage__in=valid_stages)
    sale_subject = str(filters.get("saleSubject", "")).upper()
    if sale_subject in {"FOREST", "LAND", "BOTH"}:
        queryset = queryset.filter(sale_subject=sale_subject)
    owner_status = str(filters.get("ownerStatus", "")).strip()
    if owner_status:
        queryset = queryset.filter(owner__status=owner_status)
    assignee_id = str(filters.get("assigneeId", "")).strip()
    if assignee_id:
        queryset = queryset.filter(owner__assignee_id=assignee_id)
    evaluator_id = str(filters.get("evaluatorId", "")).strip()
    if evaluator_id:
        queryset = queryset.filter(evaluator_id=evaluator_id)
    if filters.get("activeOnly", True):
        queryset = queryset.exclude(stage__in=CLOSED_DEAL_STAGES)
    stale_days = filters.get("staleDays")
    if stale_days not in (None, ""):
        try:
            days = max(1, min(int(stale_days), 730))
        except (TypeError, ValueError) as exc:
            raise ValueError("filters.staleDays must be an integer.") from exc
        queryset = queryset.filter(updated_at__lt=timezone.now() - timedelta(days=days))
    value_field = DecimalField(max_digits=16, decimal_places=2)
    queryset = queryset.annotate(segment_value=Coalesce("proposed_offer_price", "recommended_purchase_price", "price_expectation", Value(Decimal("0")), output_field=value_field))
    for key, lookup in (("minValue", "segment_value__gte"), ("maxValue", "segment_value__lte")):
        raw = filters.get(key)
        if raw not in (None, ""):
            try:
                queryset = queryset.filter(**{lookup: Decimal(str(raw))})
            except (InvalidOperation, ValueError) as exc:
                raise ValueError(f"filters.{key} must be a decimal.") from exc
    return queryset.distinct()


def _segment_or_403(request, segment_id: str):
    segment = get_object_or_404(SalesSegment, id=segment_id)
    if segment.created_by_id != request.user.id and not segment.is_shared and not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        return None, _detail("You do not have access to this sales segment.", status.HTTP_403_FORBIDDEN)
    return segment, None


def _assignment_preview_payload(request, segment: SalesSegment, target_user: User):
    deals = list(_segment_queryset(request, segment.filters).order_by("id")[:500])
    owner_ids = sorted({deal.owner_id for deal in deals})
    breakdown: dict[str, int] = {}
    for deal in deals:
        key = deal.owner.assignee_id or "UNASSIGNED"
        breakdown[key] = breakdown.get(key, 0) + 1
    token_source = json.dumps(
        {"segmentId": str(segment.id), "segmentUpdatedAt": json_value(segment.updated_at), "targetAssigneeId": target_user.id, "dealIds": sorted(str(deal.id) for deal in deals)},
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "segment": _segment_data(segment),
        "targetAssignee": user_data(target_user),
        "dealCount": len(deals),
        "ownerCount": len(owner_ids),
        "dealIds": [str(deal.id) for deal in deals],
        "ownerIds": owner_ids,
        "currentAssigneeBreakdown": breakdown,
        "previewToken": hashlib.sha256(token_source.encode("utf-8")).hexdigest(),
    }


@api_view(["GET"])
@permission_classes([CanManageSales])
def sales_funnel(request):
    try:
        from_date = _parse_date(request.query_params.get("from"), "from")
        to_date = _parse_date(request.query_params.get("to"), "to")
    except ValueError as exc:
        return _detail(str(exc))
    if from_date and to_date and from_date > to_date:
        return _detail("from must be before or equal to to.")
    queryset = _sales_base_queryset(request)
    if from_date:
        queryset = queryset.filter(created_at__date__gte=from_date)
    if to_date:
        queryset = queryset.filter(created_at__date__lte=to_date)
    segment_id = str(request.query_params.get("segmentId", "")).strip()
    segment_payload = None
    if segment_id:
        segment, denied = _segment_or_403(request, segment_id)
        if denied:
            return denied
        try:
            queryset = _segment_queryset(request, segment.filters).filter(id__in=queryset.values("id"))
        except ValueError as exc:
            return _detail(str(exc))
        segment_payload = _segment_data(segment)
    as_of = to_date or timezone.localdate()
    probability_lookup = _active_probability_lookup(as_of)
    deals = list(queryset.order_by("created_at", "id"))
    stage_index = {stage: index for index, stage in enumerate(SALES_STAGE_ORDER)}
    rows = []
    for stage in SALES_STAGE_ORDER:
        stage_deals = [deal for deal in deals if deal.stage == stage]
        entered_or_beyond = [deal for deal in deals if stage_index.get(deal.stage, 999) >= stage_index[stage]]
        beyond = [deal for deal in deals if stage_index.get(deal.stage, 999) > stage_index[stage]]
        probability, configured = probability_lookup[stage]
        values = []
        durations = []
        weighted = Decimal("0.00")
        for deal in stage_deals:
            value, source = _deal_value_basis(deal)
            values.append({"dealId": str(deal.id), "source": source, "value": value})
            end_at = deal.closed_at or deal.updated_at
            durations.append(Decimal(str(max((end_at - deal.created_at).total_seconds() / 86400, 0))))
            weighted += value * probability
        rows.append(
            {
                "stage": stage,
                "volume": len(stage_deals),
                "enteredOrBeyond": len(entered_or_beyond),
                "conversionToNext": json_value((Decimal(len(beyond)) / Decimal(len(entered_or_beyond))).quantize(Decimal("0.0001")) if entered_or_beyond else Decimal("0")),
                "medianDurationDays": json_value(_median_decimal(durations).quantize(Decimal("0.01")) if durations else Decimal("0.00")),
                "probability": json_value(probability),
                "probabilitySource": "configured" if configured else "default",
                "weightedValue": json_value(weighted.quantize(Decimal("0.01"))),
                "valueSourceBreakdown": {source: sum(1 for item in values if item["source"] == source) for source in sorted({item["source"] for item in values})},
            }
        )
    return Response(
        {
            "period": {"from": from_date.isoformat() if from_date else None, "to": to_date.isoformat() if to_date else None, "asOf": as_of.isoformat(), "generatedAt": json_value(timezone.now())},
            "segment": segment_payload,
            "formula": "weightedValue = deterministic deal value (accepted offer, proposed offer, recommended price, then price expectation) multiplied by the active stage probability as of period.to/today; WON uses 1.0 and LOST/CANCELLED use 0.0 unless configured otherwise.",
            "stages": rows,
        }
    )


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def sales_stage_probabilities(request):
    if request.method == "GET":
        stage = str(request.query_params.get("stage", "")).upper()
        records = SalesStageProbability.objects.select_related("created_by")
        if stage:
            records = records.filter(stage=stage)
        return Response([_sales_probability_data(item) for item in records[:200]])
    stage = str(request.data.get("stage", "")).upper()
    if stage not in DealStage.values:
        return _detail(f"stage must be one of: {', '.join(DealStage.values)}.")
    try:
        probability = Decimal(str(request.data.get("probability")))
        valid_from = _parse_date(request.data.get("validFrom"), "validFrom")
        valid_to = _parse_date(request.data.get("validTo"), "validTo")
    except (InvalidOperation, ValueError) as exc:
        return _detail(str(exc))
    if valid_from is None:
        return _detail("validFrom is required.")
    if probability < 0 or probability > 1:
        return _detail("probability must be between 0 and 1.")
    if valid_to and valid_to < valid_from:
        return _detail("validTo must be on or after validFrom.")
    item = SalesStageProbability.objects.create(stage=stage, probability=probability, valid_from=valid_from, valid_to=valid_to, note=str(request.data.get("note", "")).strip(), created_by=request.user)
    return Response(_sales_probability_data(item), status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAdmin])
def sales_stage_probability_detail(request, probability_id):
    item = get_object_or_404(SalesStageProbability.objects.select_related("created_by"), id=probability_id)
    if "probability" in request.data:
        try:
            probability = Decimal(str(request.data["probability"]))
        except (InvalidOperation, ValueError) as exc:
            return _detail(str(exc))
        if probability < 0 or probability > 1:
            return _detail("probability must be between 0 and 1.")
        item.probability = probability
    if "validTo" in request.data:
        try:
            item.valid_to = _parse_date(request.data.get("validTo"), "validTo")
        except ValueError as exc:
            return _detail(str(exc))
    if "note" in request.data:
        item.note = str(request.data.get("note", "")).strip()
    if item.valid_to and item.valid_to < item.valid_from:
        return _detail("validTo must be on or after validFrom.")
    item.save()
    return Response(_sales_probability_data(item))


@api_view(["GET", "POST"])
@permission_classes([CanManageSales])
def sales_segments(request):
    if request.method == "GET":
        records = SalesSegment.objects.select_related("created_by").filter(Q(created_by=request.user) | Q(is_shared=True))
        if has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
            records = SalesSegment.objects.select_related("created_by")
        return Response([_segment_data(item) for item in records[:200]])
    name = str(request.data.get("name", "")).strip()
    filters = request.data.get("filters") if isinstance(request.data.get("filters"), dict) else None
    if not name:
        return _detail("name is required.")
    if filters is None:
        return _detail("filters must be an object.")
    try:
        _segment_queryset(request, filters)[:1]
    except ValueError as exc:
        return _detail(str(exc))
    shared = bool(request.data.get("shared", False)) and has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE)
    segment = SalesSegment.objects.create(name=name[:160], filters=filters, is_shared=shared, created_by=request.user)
    return Response(_segment_data(segment), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([CanManageSales])
def sales_segment_assignment_preview(request, segment_id):
    segment, denied = _segment_or_403(request, str(segment_id))
    if denied:
        return denied
    target_id = str(request.data.get("targetAssigneeId", "")).strip()
    if not target_id:
        return _detail("targetAssigneeId is required.")
    target = organization_user_or_404(request, target_id, active_only=True)
    try:
        return Response(_assignment_preview_payload(request, segment, target))
    except ValueError as exc:
        return _detail(str(exc))


@api_view(["POST"])
@permission_classes([CanManageSales])
def sales_segment_assignment_apply(request, segment_id):
    segment, denied = _segment_or_403(request, str(segment_id))
    if denied:
        return denied
    target_id = str(request.data.get("targetAssigneeId", "")).strip()
    token = str(request.data.get("previewToken", "")).strip()
    if not target_id or not token:
        return _detail("targetAssigneeId and previewToken are required.")
    target = organization_user_or_404(request, target_id, active_only=True)
    try:
        preview = _assignment_preview_payload(request, segment, target)
    except ValueError as exc:
        return _detail(str(exc))
    if token != preview["previewToken"]:
        return _detail("Preview token is stale; refresh the assignment preview before applying.", status.HTTP_409_CONFLICT)
    owners = Owner.objects.filter(id__in=preview["ownerIds"])
    if not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        owners = owners.filter(assignee=request.user)
    changed = 0
    with transaction.atomic():
        for owner in owners.select_for_update():
            if owner.assignee_id == target.id:
                continue
            owner.assignee = target
            owner.version += 1
            owner.save(update_fields=("assignee", "version"))
            OwnerLog.objects.create(owner=owner, creator=request.user, message=f"Sales segment assignment applied from segment {segment.name} to {target.full_name}.")
            changed += 1
    preview["changedOwnerCount"] = changed
    return Response(preview)


@api_view(["GET"])
@permission_classes([CanManageOwners])
def owner_cursor_list(request):
    """Stable keyset owner search. The cursor is opaque and page size is bounded."""
    try:
        cursor = _decode_cursor(request.query_params.get("cursor"))
        limit = _limit(request)
    except ValueError as exc:
        return _detail(str(exc))
    queryset = Owner.objects.select_related("assignee").order_by("id")
    if not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        queryset = queryset.filter(assignee=request.user)
    query = str(request.query_params.get("q", "")).strip()
    if query:
        queryset = queryset.filter(Q(id__icontains=query) | Q(name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query))
    statuses = str(request.query_params.get("statuses", "")).strip()
    if statuses:
        queryset = queryset.filter(status__in=[value for value in statuses.split(",") if value])
    if cursor:
        queryset = queryset.filter(id__gt=cursor)
    records = list(queryset[: limit + 1])
    has_more = len(records) > limit
    records = records[:limit]
    return Response({
        "items": [owner_summary(owner) for owner in records],
        "nextCursor": _encode_cursor(records[-1].id) if has_more and records else None,
        "pageSize": limit,
    })


@api_view(["GET", "POST"])
@permission_classes([CanManageOwners])
def owner_activities(request, owner_id: str):
    owner, denied = _owner_or_403(request, owner_id)
    if denied:
        return denied
    if request.method == "GET":
        records = ContactActivity.objects.filter(owner=owner).select_related("created_by", "deal").prefetch_related("next_actions__assignee")[:200]
        return Response([_activity_data(item) for item in records])

    channel = str(request.data.get("channel", "")).upper()
    if channel not in ContactActivity.Channel.values:
        return _detail("channel must be PHONE, EMAIL or MEETING.")
    outcome_code = str(request.data.get("outcomeCode", "")).strip().upper()
    if not outcome_code:
        return _detail("outcomeCode is required.")
    deal = None
    deal_id = request.data.get("dealId")
    if deal_id:
        deal, denied = _deal_or_403(request, str(deal_id))
        if denied:
            return denied
        if deal.owner_id != owner.id:
            return _detail("The selected deal does not belong to this owner.")
    next_payload = request.data.get("nextAction") if isinstance(request.data.get("nextAction"), dict) else None
    try:
        with transaction.atomic():
            activity = ContactActivity.objects.create(
                owner=owner,
                deal=deal,
                channel=channel,
                outcome_code=outcome_code,
                outcome_reason=str(request.data.get("outcomeReason", "")).strip(),
                note=str(request.data.get("note", "")).strip(),
                created_by=request.user,
            )
            action = None
            if next_payload:
                text = str(next_payload.get("text", "")).strip()
                due_at = _parse_datetime(next_payload.get("dueAt"), "nextAction.dueAt")
                if not text or due_at is None:
                    raise ValueError("nextAction requires text and dueAt.")
                assignee_id = str(next_payload.get("assigneeId") or request.user.id)
                assignee = organization_user_or_404(request, assignee_id, active_only=True)
                action = NextAction.objects.create(
                    owner=owner,
                    deal=deal,
                    source_activity=activity,
                    text=text,
                    due_at=due_at,
                    assignee=assignee,
                    created_by=request.user,
                )
            _audit(owner=owner, deal=deal, activity=activity, actor=request.user, event_type="CONTACT_RECORDED", payload={"channel": channel, "outcomeCode": outcome_code})
            if action:
                _audit(owner=owner, deal=deal, activity=activity, next_action=action, actor=request.user, event_type="NEXT_ACTION_CREATED", payload={"dueAt": json_value(action.due_at), "assigneeId": action.assignee_id})
    except ValueError as exc:
        return _detail(str(exc))
    return Response(_activity_data(activity), status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([CanManageOwners])
def next_action_detail(request, action_id):
    action = get_object_or_404(NextAction.objects.select_related("owner", "deal", "assignee"), id=action_id)
    if not can_access_owner(request, action.owner) and (not action.deal or not can_access_deal(request, action.deal)):
        return _detail("You do not have access to this next action.", status.HTTP_403_FORBIDDEN)
    operation = str(request.data.get("operation", "")).upper()
    payload = {}
    if operation == "COMPLETE":
        action.status = NextAction.Status.DONE
        action.completed_at = timezone.now()
    elif operation == "POSTPONE":
        try:
            due_at = _parse_datetime(request.data.get("dueAt"), "dueAt")
        except ValueError as exc:
            return _detail(str(exc))
        if due_at is None:
            return _detail("dueAt is required when postponing.")
        payload["previousDueAt"] = json_value(action.due_at)
        action.due_at = due_at
        action.status = NextAction.Status.POSTPONED
        action.completed_at = None
    elif operation == "DELEGATE":
        assignee_id = str(request.data.get("assigneeId", "")).strip()
        if not assignee_id:
            return _detail("assigneeId is required when delegating.")
        payload["previousAssigneeId"] = action.assignee_id
        action.assignee = organization_user_or_404(request, assignee_id, active_only=True)
        action.status = NextAction.Status.OPEN
    else:
        return _detail("operation must be COMPLETE, POSTPONE or DELEGATE.")
    payload.update({"status": action.status, "dueAt": json_value(action.due_at), "assigneeId": action.assignee_id})
    action.save()
    _audit(owner=action.owner, deal=action.deal, next_action=action, actor=request.user, event_type=f"NEXT_ACTION_{operation}", payload=payload)
    return Response(_action_data(action))


@api_view(["GET"])
@permission_classes([CanManageOwners])
def owner_timeline(request, owner_id: str):
    owner, denied = _owner_or_403(request, owner_id)
    if denied:
        return denied
    events = WorkflowAuditEvent.objects.filter(owner=owner).select_related("actor")[:300]
    return Response([_event_data(event) for event in events])


@api_view(["GET"])
@permission_classes([CanManageOwners])
def owner_360_summary(request, owner_id: str):
    owner, denied = _owner_or_403(request, owner_id)
    if denied:
        return denied
    relation_counts = _owner_relation_counts(owner)
    cadastre_count = OwnershipRelation.objects.filter(owner=owner, is_active=True).values("cadastre_id").distinct().count()
    if cadastre_count == 0:
        cadastre_count = OwnerCadastre.objects.filter(owner=owner).count()
    action_count = NextAction.objects.filter(owner=owner, status__in=(NextAction.Status.OPEN, NextAction.Status.POSTPONED)).count()
    active_deal_count = Deal.objects.filter(owner=owner).exclude(stage__in=CLOSED_DEAL_STAGES).count()
    contact_fields = [owner.phone, owner.email, owner.address]
    contact_completeness = round(100 * sum(1 for item in contact_fields if item) / len(contact_fields))
    signals = []
    if contact_completeness < 67:
        signals.append({"code": "CONTACT_INCOMPLETE", "severity": "MEDIUM", "message": "Owner contact data is incomplete."})
    if action_count:
        signals.append({"code": "OPEN_NEXT_ACTIONS", "severity": "LOW", "message": "Open owner workflow actions need follow-up."})
    if active_deal_count:
        signals.append({"code": "ACTIVE_DEALS", "severity": "LOW", "message": "Owner has active commercial work."})
    return Response(
        {
            "owner": owner_summary(owner),
            "contactCompleteness": contact_completeness,
            "cadastreCount": cadastre_count,
            "relations": relation_counts,
            "openNextActionCount": action_count,
            "activeDealCount": active_deal_count,
            "signalCount": len(signals),
            "signals": signals,
            "panels": {
                "relations": f"/api/services/owners/{owner.id}/ownership-relations",
                "map": f"/api/services/owners/{owner.id}/360/map",
                "timeline": f"/api/services/owners/{owner.id}/360/timeline",
                "workflow": f"/api/services/owners/{owner.id}/360/workflow",
            },
        }
    )


@api_view(["GET"])
@permission_classes([CanManageOwners])
def owner_360_map(request, owner_id: str):
    owner, denied = _owner_or_403(request, owner_id)
    if denied:
        return denied
    _project_legacy_relations(owner)
    relations = (
        OwnershipRelation.objects.filter(owner=owner, is_active=True)
        .select_related("cadastre")
        .order_by("cadastre_id")[:500]
    )
    return Response({"type": "FeatureCollection", "features": [_owner_map_feature(relation) for relation in relations]})


@api_view(["GET"])
@permission_classes([CanManageOwners])
def owner_360_workflow(request, owner_id: str):
    owner, denied = _owner_or_403(request, owner_id)
    if denied:
        return denied
    actions = NextAction.objects.filter(owner=owner, status__in=(NextAction.Status.OPEN, NextAction.Status.POSTPONED)).select_related("assignee").order_by("due_at", "id")[:8]
    deals = Deal.objects.filter(owner=owner).exclude(stage__in=CLOSED_DEAL_STAGES).select_related("created_by", "evaluator").prefetch_related("next_actions__assignee").order_by("-updated_at")[:8]
    transitions = OwnershipTransitionEvent.objects.filter(owner=owner).order_by("-occurred_at", "-recorded_at")[:5]
    signals = []
    now = timezone.now()
    for action in actions:
        if action.due_at < now:
            signals.append({"code": "NEXT_ACTION_OVERDUE", "severity": "HIGH", "message": action.text, "target": {"nextActionId": str(action.id)}})
    for deal in deals:
        reasons, _, _ = _deal_health(deal)
        signals.extend({**reason, "target": {"dealId": str(deal.id)}} for reason in reasons[:2])
    return Response(
        {
            "nextActions": [_action_data(action) for action in actions],
            "activeDeals": [_deal_work_item(deal) for deal in deals],
            "recentOwnershipChanges": [
                {
                    "id": str(item.id),
                    "cadastreId": item.cadastre_id,
                    "type": item.event_type,
                    "occurredAt": json_value(item.occurred_at),
                    "sourceReference": item.source_reference or None,
                    "recordedAt": json_value(item.recorded_at),
                }
                for item in transitions
            ],
            "signals": signals[:12],
        }
    )


@api_view(["GET"])
@permission_classes([CanManageOwners])
def owner_360_timeline(request, owner_id: str):
    owner, denied = _owner_or_403(request, owner_id)
    if denied:
        return denied
    try:
        limit = _limit(request, default=50, maximum=100)
    except ValueError as exc:
        return _detail(str(exc))
    items = []
    for activity in ContactActivity.objects.filter(owner=owner).select_related("created_by").order_by("-created_at")[:100]:
        items.append(
            _owner_360_timeline_item(
                "CONTACT",
                "contact_activity",
                str(activity.id),
                activity.created_at,
                f"{activity.channel} · {activity.outcome_code}",
                activity.outcome_reason or activity.note,
                {"activityId": str(activity.id)},
                activity.created_by,
            )
        )
    for action in NextAction.objects.filter(owner=owner).select_related("assignee", "created_by").order_by("-created_at")[:100]:
        items.append(
            _owner_360_timeline_item(
                "NEXT_ACTION",
                "next_action",
                str(action.id),
                action.completed_at or action.due_at,
                action.text,
                action.status,
                {"nextActionId": str(action.id), "dealId": str(action.deal_id) if action.deal_id else None},
                action.assignee,
                {"status": action.status},
            )
        )
    for deal in Deal.objects.filter(owner=owner).select_related("created_by").order_by("-updated_at")[:100]:
        items.append(
            _owner_360_timeline_item(
                "DEAL",
                "deal",
                str(deal.id),
                deal.closed_at or deal.updated_at,
                f"Deal {deal.stage.replace('_', ' ').title()}",
                deal.sale_subject,
                {"dealId": str(deal.id)},
                deal.created_by,
                {"stage": deal.stage, "saleSubject": deal.sale_subject},
            )
        )
    for contract in Contract.objects.filter(source_deal__owner=owner).select_related("source_deal").order_by("-created_at")[:100]:
        items.append(
            _owner_360_timeline_item(
                "CONTRACT",
                "contract",
                contract.id,
                contract.created_at,
                f"Contract {contract.status.lower()}",
                contract.base_id or contract.id,
                {"contractId": contract.id, "dealId": str(contract.source_deal_id) if contract.source_deal_id else None},
            )
        )
    for relation in OwnershipRelation.objects.filter(owner=owner).select_related("cadastre").order_by("-valid_from")[:100]:
        occurred_at = relation.valid_to or relation.valid_from
        title = "Ownership relation active" if relation.is_active else "Ownership relation ended"
        items.append(
            _owner_360_timeline_item(
                "OWNERSHIP_RELATION",
                "ownership_relation",
                str(relation.id),
                occurred_at,
                title,
                relation.cadastre.name or relation.cadastre_id,
                {"relationId": str(relation.id), "cadastreId": relation.cadastre_id},
                relation.updated_by or relation.created_by,
                {"active": relation.is_active, "source": relation.source},
            )
        )
    for transition in OwnershipTransitionEvent.objects.filter(owner=owner).order_by("-occurred_at", "-recorded_at")[:100]:
        items.append(
            _owner_360_timeline_item(
                "OWNERSHIP_CHANGE",
                "ownership_transition",
                str(transition.id),
                transition.occurred_at or transition.recorded_at,
                transition.event_type.replace("_", " ").title(),
                transition.source_reference,
                {"transitionId": str(transition.id), "cadastreId": transition.cadastre_id},
                payload=transition.payload,
            )
        )
    for event in WorkflowAuditEvent.objects.filter(owner=owner).select_related("actor").order_by("-created_at")[:100]:
        items.append(
            _owner_360_timeline_item(
                "WORKFLOW_AUDIT",
                "workflow_audit",
                str(event.id),
                event.created_at,
                event.event_type.replace("_", " ").title(),
                "",
                {"eventId": str(event.id), "dealId": str(event.deal_id) if event.deal_id else None},
                event.actor,
                event.payload,
            )
        )
    items.sort(key=lambda item: item["occurredAt"] or 0, reverse=True)
    return Response(items[:limit])


@api_view(["GET"])
@permission_classes([CanManageOwners])
def deal_timeline(request, deal_id: str):
    deal, denied = _deal_or_403(request, deal_id)
    if denied:
        return denied
    events = WorkflowAuditEvent.objects.filter(deal=deal).select_related("actor")[:300]
    return Response([_event_data(event) for event in events])


def _deal_health(deal: Deal) -> tuple[list[dict], NextAction | None, DealWorkState | None]:
    now = timezone.now()
    action = next((item for item in deal.next_actions.all() if item.status in (NextAction.Status.OPEN, NextAction.Status.POSTPONED)), None)
    try:
        work_state = deal.work_state
    except DealWorkState.DoesNotExist:
        work_state = None
    reasons = []
    if action is None:
        reasons.append({"code": "NO_NEXT_ACTION", "severity": "HIGH", "message": "No next action is scheduled."})
    elif action.due_at < now:
        reasons.append({"code": "NEXT_ACTION_OVERDUE", "severity": "HIGH", "message": "The next action is overdue."})
    if deal.stage == DealStage.EVALUATION:
        if not work_state or not work_state.evaluation_due_at:
            reasons.append({"code": "EVALUATION_DEADLINE_MISSING", "severity": "HIGH", "message": "Evaluation deadline is missing."})
        elif work_state.evaluation_due_at < now:
            reasons.append({"code": "EVALUATION_SLA_OVERDUE", "severity": "CRITICAL", "message": "Evaluation SLA deadline is overdue."})
    if deal.stage == DealStage.NEGOTIATION and deal.offer_valid_until and deal.offer_valid_until <= date.today() + timedelta(days=3):
        reasons.append({"code": "OFFER_EXPIRING", "severity": "MEDIUM", "message": "Offer expires within three days."})
    if deal.updated_at < now - timedelta(days=7):
        reasons.append({"code": "INACTIVE", "severity": "MEDIUM", "message": "Deal has had no aggregate activity for seven days."})
    return reasons, action, work_state


def _deal_work_item(deal: Deal) -> dict:
    reasons, action, work_state = _deal_health(deal)
    value = deal.proposed_offer_price or deal.recommended_purchase_price or deal.price_expectation
    responsible = action.assignee if action else (deal.evaluator or deal.created_by)
    return {
        "id": str(deal.id),
        "version": deal.version,
        "owner": owner_summary(deal.owner),
        "stage": deal.stage,
        "value": json_value(value),
        "responsible": user_data(responsible),
        "nextAction": _action_data(action),
        "evaluationDueAt": json_value(work_state.evaluation_due_at) if work_state else None,
        "offerValidUntil": deal.offer_valid_until.isoformat() if deal.offer_valid_until else None,
        "updatedAt": json_value(deal.updated_at),
        "health": reasons,
        "healthy": not reasons,
    }


def _decision_evidence_signal(code: str, severity: str, reason: str, source: str, observed_at, recommended_action: str, target: dict | None = None) -> dict:
    return {
        "code": code,
        "severity": severity,
        "reason": reason,
        "source": source,
        "observedAt": _snapshot_json_value(observed_at),
        "recommendedAction": recommended_action,
        "target": target or {},
    }


def _decision_evidence_source(name: str, observed_at, status: str = "OBSERVED") -> dict:
    return {"source": name, "observedAt": _snapshot_json_value(observed_at), "status": status}


def _snapshot_json_value(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    return json_value(value)


def _build_decision_evidence_snapshot(deal: Deal, *, decision_type: str) -> dict:
    now = timezone.now()
    owner = deal.owner
    cadastres = deal.parcels.prefetch_related("labels").all()
    cadastre_ids = list(cadastres.values_list("id", flat=True))
    cadastre_totals = cadastres.aggregate(total_area=Sum("area"), forest_area=Sum("forest_area"), latest_mk_date=Max("mk_date"))
    notifications = CadastreNotification.objects.filter(cadastre_id__in=cadastre_ids)
    active_notifications = notifications.filter(archived=False)
    notification_totals = notifications.aggregate(latest_registration=Max("registration_date"))
    registry_features = ForestRegistryFeature.objects.filter(cadastre_id__in=cadastre_ids)
    registry_totals = registry_features.aggregate(known_volume=Sum("volume"), latest_event=Max("event_date"))
    active_deals = Deal.objects.filter(owner=owner).exclude(stage__in=CLOSED_DEAL_STAGES)
    signals = []
    if not owner.phone or not owner.email:
        missing = ", ".join(item for item, empty in (("phone", not owner.phone), ("email", not owner.email)) if empty)
        signals.append(_decision_evidence_signal("MISSING_CONTACT", "HIGH", f"Owner is missing {missing}.", "owner", now, "Complete owner contact data.", {"ownerId": owner.id}))
    if owner.last_cadastre_list_refresh is None or owner.last_cadastre_list_refresh < now - timedelta(days=90):
        signals.append(_decision_evidence_signal("STALE_REGISTRY_DATA", "MEDIUM", "Owner cadastre list has not been refreshed within 90 days.", "owner.lastCadastreListRefresh", owner.last_cadastre_list_refresh, "Refresh the owner portfolio before making an offer.", {"ownerId": owner.id}))
    fresh_cutoff = now - timedelta(days=30)
    for notice in active_notifications.filter(registration_date__gte=fresh_cutoff).order_by("-registration_date", "-id")[:5]:
        signals.append(_decision_evidence_signal("FRESH_FOREST_NOTICE", "MEDIUM", f"Active forest notice {notice.notification_number} was registered recently.", "metsaregister.notifications", notice.registration_date, "Review the notice before valuation.", {"cadastreId": notice.cadastre_id, "notificationId": notice.id}))
    restricted_labels = {"CONSERVATION_AREA", "DEAD_LAND", "SWAMP"}
    selected_cadastres = []
    for cadastre in cadastres:
        labels = sorted(label.code for label in cadastre.labels.all())
        restricted = [label for label in labels if label in restricted_labels]
        if restricted:
            signals.append(_decision_evidence_signal("RESTRICTION_LABEL", "MEDIUM", f"Cadastre has restriction labels: {', '.join(restricted)}.", "cadastre.labels", now, "Check restrictions before valuation.", {"cadastreId": cadastre.id, "labels": restricted}))
        selected_cadastres.append(
            {
                "id": cadastre.id,
                "name": cadastre.name or None,
                "county": cadastre.county or None,
                "area": json_value(cadastre.area),
                "forestArea": json_value(cadastre.forest_area),
                "mkDate": json_value(cadastre.mk_date),
                "labels": labels,
            }
        )
    offer_cutoff = date.today() + timedelta(days=7)
    for related_deal in active_deals.filter(offer_valid_until__isnull=False, offer_valid_until__lte=offer_cutoff).order_by("offer_valid_until", "id")[:5]:
        signals.append(_decision_evidence_signal("OFFER_DEADLINE_APPROACHING", "HIGH", f"Active {related_deal.stage.lower()} deal offer deadline is approaching.", "commercial_deals.offer_valid_until", related_deal.offer_valid_until, "Contact the owner or update the offer plan.", {"dealId": str(related_deal.id)}))
    latest_offer = deal.offers.order_by("-revision", "-created_at").first()
    freshness = [
        _decision_evidence_source("owner.lastCadastreListRefresh", owner.last_cadastre_list_refresh, "STALE" if owner.last_cadastre_list_refresh is None or owner.last_cadastre_list_refresh < now - timedelta(days=90) else "OBSERVED"),
        _decision_evidence_source("cadastre.mkDate", cadastre_totals["latest_mk_date"], "MISSING" if cadastre_totals["latest_mk_date"] is None else "OBSERVED"),
        _decision_evidence_source("metsaregister.notifications", notification_totals["latest_registration"], "MISSING" if notification_totals["latest_registration"] is None else "OBSERVED"),
        _decision_evidence_source("metsaregister.registryFeatures", registry_totals["latest_event"], "MISSING" if registry_totals["latest_event"] is None else "OBSERVED"),
    ]
    return {
        "schemaVersion": DECISION_EVIDENCE_SCHEMA_VERSION,
        "decisionType": decision_type,
        "generatedAt": json_value(now),
        "deal": {
            "id": str(deal.id),
            "version": deal.version,
            "stage": deal.stage,
            "saleSubject": deal.sale_subject,
            "evaluationStatus": deal.evaluation_status or None,
            "estimatedMinPrice": json_value(deal.estimated_min_price),
            "estimatedMaxPrice": json_value(deal.estimated_max_price),
            "recommendedPurchasePrice": json_value(deal.recommended_purchase_price),
            "internalMinPrice": json_value(deal.internal_min_price),
            "proposedOfferPrice": json_value(deal.proposed_offer_price),
            "offerValidUntil": deal.offer_valid_until.isoformat() if deal.offer_valid_until else None,
            "latestOffer": {
                "id": str(latest_offer.id),
                "revision": latest_offer.revision,
                "status": latest_offer.status,
                "amount": json_value(latest_offer.amount),
                "validUntil": latest_offer.valid_until.isoformat() if latest_offer.valid_until else None,
            } if latest_offer else None,
        },
        "owner": owner_summary(owner),
        "selectedCadastres": sorted(selected_cadastres, key=lambda item: item["id"]),
        "portfolioSummary": {
            "cadastreCount": len(cadastre_ids),
            "totalArea": json_value(cadastre_totals["total_area"]),
            "forestArea": json_value(cadastre_totals["forest_area"]),
            "knownVolume": json_value(registry_totals["known_volume"]),
            "activeNoticeCount": active_notifications.count(),
            "activeDealCount": active_deals.count(),
        },
        "countyBreakdown": [
            {"county": item["county"] or None, "cadastreCount": item["count"], "area": json_value(item["area"])}
            for item in cadastres.values("county").annotate(count=Count("id"), area=Sum("area")).order_by("county")
        ],
        "freshness": freshness,
        "signals": signals,
    }


def _decision_snapshot_hash(snapshot: dict) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _decision_snapshot_data(item: DecisionEvidenceSnapshot) -> dict:
    return {
        "id": str(item.id),
        "dealId": str(item.deal_id),
        "sequence": item.sequence,
        "decisionType": item.decision_type,
        "schemaVersion": item.schema_version,
        "snapshot": item.snapshot,
        "snapshotSha256": item.snapshot_sha256,
        "confirmedBy": user_data(item.confirmed_by),
        "confirmedAt": json_value(item.confirmed_at),
    }


@api_view(["GET"])
@permission_classes([CanManageOwners])
def deal_decision_evidence_preview(request, deal_id: str):
    deal, denied = _deal_or_403(request, deal_id)
    if denied:
        return denied
    decision_type = str(request.query_params.get("decisionType", DecisionEvidenceSnapshot.DecisionType.EVALUATION)).upper()
    if decision_type not in DecisionEvidenceSnapshot.DecisionType.values:
        return _detail("decisionType must be EVALUATION or OFFER.")
    snapshot = _build_decision_evidence_snapshot(deal, decision_type=decision_type)
    return Response({"snapshot": snapshot, "snapshotSha256": _decision_snapshot_hash(snapshot)})


@api_view(["GET", "POST"])
@permission_classes([CanManageOwners])
def deal_decision_evidence_snapshots(request, deal_id: str):
    deal, denied = _deal_or_403(request, deal_id)
    if denied:
        return denied
    if request.method == "GET":
        records = deal.decision_evidence_snapshots.select_related("confirmed_by").all()
        return Response([_decision_snapshot_data(item) for item in records])
    decision_type = str(request.data.get("decisionType", DecisionEvidenceSnapshot.DecisionType.EVALUATION)).upper()
    if decision_type not in DecisionEvidenceSnapshot.DecisionType.values:
        return _detail("decisionType must be EVALUATION or OFFER.")
    snapshot = _build_decision_evidence_snapshot(deal, decision_type=decision_type)
    with transaction.atomic():
        locked = Deal.objects.select_for_update().get(id=deal.id)
        sequence = (DecisionEvidenceSnapshot.objects.filter(deal=locked).aggregate(last=Max("sequence"))["last"] or 0) + 1
        item = DecisionEvidenceSnapshot.objects.create(
            deal=locked,
            sequence=sequence,
            decision_type=decision_type,
            schema_version=DECISION_EVIDENCE_SCHEMA_VERSION,
            snapshot=snapshot,
            snapshot_sha256=_decision_snapshot_hash(snapshot),
            confirmed_by=request.user,
        )
        _audit(owner=locked.owner, deal=locked, actor=request.user, event_type="DECISION_EVIDENCE_CONFIRMED", payload={"snapshotId": str(item.id), "sequence": item.sequence, "decisionType": decision_type})
    return Response(_decision_snapshot_data(item), status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([CanManageOwners])
def deal_workbench(request):
    queryset = Deal.objects.select_related("owner", "owner__assignee", "evaluator", "created_by").prefetch_related("next_actions__assignee").exclude(stage__in=CLOSED_DEAL_STAGES)
    if not has_membership_privilege(request, PrivilegeCode.ADMIN, PrivilegeCode.OWNER_PROFILE):
        queryset = queryset.filter(Q(owner__assignee=request.user) | Q(evaluator=request.user)).distinct()
    stage_filter = str(request.query_params.get("stage", "")).strip()
    if stage_filter:
        queryset = queryset.filter(stage=stage_filter)
    responsible = str(request.query_params.get("responsibleId", "")).strip()
    if responsible:
        queryset = queryset.filter(Q(next_actions__assignee_id=responsible, next_actions__status__in=[NextAction.Status.OPEN, NextAction.Status.POSTPONED]) | Q(evaluator_id=responsible) | Q(created_by_id=responsible)).distinct()
    value_field = DecimalField(max_digits=14, decimal_places=2)
    queryset = queryset.annotate(work_value=Coalesce("proposed_offer_price", "recommended_purchase_price", "price_expectation", Value(Decimal("0")), output_field=value_field))
    for key, lookup in (("minValue", "work_value__gte"), ("maxValue", "work_value__lte")):
        raw = request.query_params.get(key)
        if raw not in (None, ""):
            try:
                queryset = queryset.filter(**{lookup: Decimal(str(raw))})
            except (InvalidOperation, ValueError):
                return _detail(f"{key} must be a decimal.")
    try:
        limit = _limit(request, default=100, maximum=200)
    except ValueError as exc:
        return _detail(str(exc))
    items = [_deal_work_item(deal) for deal in queryset.order_by("updated_at", "id")[:limit]]
    health = str(request.query_params.get("health", "")).strip().upper()
    if health:
        items = [item for item in items if any(reason["code"] == health for reason in item["health"])]
    deadline_before = request.query_params.get("deadlineBefore")
    if deadline_before:
        try:
            cutoff = _parse_datetime(deadline_before, "deadlineBefore")
        except ValueError as exc:
            return _detail(str(exc))
        items = [item for item in items if item["nextAction"] and datetime.fromtimestamp(item["nextAction"]["dueAt"] / 1000, tz=timezone.get_current_timezone()) <= cutoff]
    return Response(items)


@api_view(["POST"])
@permission_classes([CanManageOwners])
def deal_next_action(request, deal_id: str):
    deal, denied = _deal_or_403(request, deal_id)
    if denied:
        return denied
    text = str(request.data.get("text", "")).strip()
    try:
        due_at = _parse_datetime(request.data.get("dueAt"), "dueAt")
        evaluation_due = _parse_datetime(request.data.get("evaluationDueAt"), "evaluationDueAt") if "evaluationDueAt" in request.data else None
    except ValueError as exc:
        return _detail(str(exc))
    if not text or due_at is None:
        return _detail("text and dueAt are required.")
    assignee = organization_user_or_404(request, str(request.data.get("assigneeId") or request.user.id), active_only=True)
    with transaction.atomic():
        action = NextAction.objects.create(owner=deal.owner, deal=deal, text=text, due_at=due_at, assignee=assignee, created_by=request.user)
        if "evaluationDueAt" in request.data:
            state, _ = DealWorkState.objects.get_or_create(deal=deal)
            state.evaluation_due_at = evaluation_due
            state.save()
        _audit(owner=deal.owner, deal=deal, next_action=action, actor=request.user, event_type="NEXT_ACTION_CREATED", payload={"dueAt": json_value(due_at), "assigneeId": assignee.id})
    return Response(_action_data(action), status=status.HTTP_201_CREATED)


def _ensure_default_loss_reasons():
    for code, label, order in DEFAULT_LOSS_REASONS:
        LossReasonCode.objects.get_or_create(code=code, defaults={"label": label, "sort_order": order})


def _loss_reason_data(item: LossReasonCode):
    return {"id": str(item.id), "code": item.code, "label": item.label, "description": item.description or None, "active": item.is_active, "sortOrder": item.sort_order}


@api_view(["GET", "POST"])
@permission_classes([CanManageOwners])
def loss_reasons(request):
    _ensure_default_loss_reasons()
    if request.method == "GET":
        active_only = request.query_params.get("active", "true").lower() != "false"
        records = LossReasonCode.objects.all()
        if active_only:
            records = records.filter(is_active=True)
        return Response([_loss_reason_data(item) for item in records])
    if not has_membership_privilege(request, PrivilegeCode.ADMIN):
        return _detail("Administrator privilege is required.", status.HTTP_403_FORBIDDEN)
    code = str(request.data.get("code", "")).strip().upper()
    label = str(request.data.get("label", "")).strip()
    if not code or not label or not re.fullmatch(r"[A-Z0-9_]{2,50}", code):
        return _detail("code must use 2-50 uppercase letters, digits or underscores and label is required.")
    if LossReasonCode.objects.filter(code=code).exists():
        return _detail("A loss reason with this code already exists.", status.HTTP_409_CONFLICT)
    item = LossReasonCode.objects.create(code=code, label=label, description=str(request.data.get("description", "")).strip(), sort_order=int(request.data.get("sortOrder", 100)))
    return Response(_loss_reason_data(item), status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAdmin])
def loss_reason_detail(request, reason_id):
    item = get_object_or_404(LossReasonCode, id=reason_id)
    for field, key in (("label", "label"), ("description", "description"), ("is_active", "active"), ("sort_order", "sortOrder")):
        if key in request.data:
            setattr(item, field, request.data[key])
    item.save()
    return Response(_loss_reason_data(item))


@api_view(["POST"])
@permission_classes([CanManageOwners])
def deal_lost_structured(request, deal_id: str):
    deal, denied = _deal_or_403(request, deal_id)
    if denied:
        return denied
    if deal.stage in CLOSED_DEAL_STAGES:
        return _detail("Closed deals cannot be lost again.", status.HTTP_409_CONFLICT)
    _ensure_default_loss_reasons()
    reason_code = str(request.data.get("reasonCode") or request.data.get("lossReason") or "").strip().upper()
    reason = LossReasonCode.objects.filter(code=reason_code, is_active=True).first()
    if reason is None:
        return _detail("An active managed reasonCode is required.")
    note = str(request.data.get("note", "")).strip()
    try:
        follow_up = _parse_datetime(request.data.get("followUpAt"), "followUpAt") if request.data.get("followUpAt") else None
    except ValueError as exc:
        return _detail(str(exc))
    previous_stage = deal.stage
    now = timezone.now()
    with transaction.atomic():
        updated, conflict = _update_deal_or_conflict(request, deal, stage=DealStage.LOST, loss_reason=reason.code, closed_at=now)
        if conflict:
            return conflict
        outcome = DealLossOutcome.objects.create(deal=updated, reason=reason, previous_stage=previous_stage, note=note, follow_up_at=follow_up, recorded_by=request.user)
        action = None
        if follow_up:
            action = NextAction.objects.create(owner=updated.owner, deal=updated, text=f"Follow up after lost deal: {reason.label}", due_at=follow_up, assignee=request.user, created_by=request.user)
        OwnerLog.objects.create(owner=updated.owner, creator=request.user, message=f"Deal {updated.id} LOST: {reason.code}{f' — {note}' if note else ''}")
        _audit(owner=updated.owner, deal=updated, next_action=action, actor=request.user, event_type="DEAL_LOST", payload={"reasonCode": reason.code, "previousStage": previous_stage, "followUpAt": json_value(follow_up)})
    return Response({"state": _commercial(updated), "loss": {"reason": _loss_reason_data(reason), "note": outcome.note, "followUpAt": json_value(outcome.follow_up_at), "nextAction": _action_data(action)}})


@api_view(["GET"])
@permission_classes([IsAdmin])
def loss_analysis(request):
    records = DealLossOutcome.objects.select_related("reason", "deal", "deal__created_by")
    for key, lookup in (("from", "created_at__date__gte"), ("to", "created_at__date__lte")):
        raw = request.query_params.get(key)
        if raw:
            try:
                records = records.filter(**{lookup: date.fromisoformat(raw)})
            except ValueError:
                return _detail(f"{key} must use YYYY-MM-DD.")
    seller_id = str(request.query_params.get("sellerId", "")).strip()
    if seller_id:
        records = records.filter(deal__created_by_id=seller_id)
    previous_stage = str(request.query_params.get("previousStage", "")).strip()
    if previous_stage:
        records = records.filter(previous_stage=previous_stage)
    grouped = defaultdict(lambda: {"count": 0})
    for item in records:
        key = (item.reason.code, item.reason.label, item.deal.created_by_id, item.previous_stage)
        grouped[key]["count"] += 1
    return Response([
        {"reasonCode": key[0], "reasonLabel": key[1], "sellerId": key[2], "previousStage": key[3], "count": value["count"]}
        for key, value in sorted(grouped.items(), key=lambda pair: (-pair[1]["count"], pair[0]))
    ])


def _signing_data(signing: ContractSigning):
    return {
        "contractId": signing.contract_id,
        "state": signing.state,
        "responsible": user_data(signing.responsible),
        "dueAt": json_value(signing.due_at),
        "delayReason": signing.delay_reason or None,
        "finalDocument": signing.final_document.name if signing.final_document else None,
        "finalUrl": signing.final_url or None,
        "finalContentType": signing.final_content_type or None,
        "verification": {
            "status": signing.verification_status,
            "documentSha256": signing.document_sha256 or None,
            "verifiedAt": json_value(signing.verified_at),
            "reference": signing.verification_reference or None,
            "signer": signing.signer_metadata or None,
            "certificate": signing.certificate_metadata or None,
            "failureReason": signing.verification_failure_reason or None,
            "integrityValid": stored_file_integrity(signing.final_document, signing.document_sha256),
        },
        "version": signing.version,
        "updatedAt": json_value(signing.updated_at),
        "events": [
            {"id": str(event.id), "fromState": event.from_state or None, "toState": event.to_state, "reason": event.reason or None, "actor": user_data(event.actor), "metadata": event.metadata, "createdAt": json_value(event.created_at)}
            for event in signing.events.select_related("actor").all()
        ],
    }


def _get_signing(contract: Contract):
    signing, created = ContractSigning.objects.get_or_create(contract=contract)
    if created:
        ContractSigningEvent.objects.create(signing=signing, from_state="", to_state=signing.state, event_type="" if False else None) if False else None
    return signing


@api_view(["GET", "PATCH"])
@permission_classes([IsAdmin])
def contract_signing(request, contract_id: str):
    contract = get_object_or_404(Contract.objects, id=contract_id)
    signing = _get_signing(contract)
    if request.method == "GET":
        return Response(_signing_data(signing))
    expected = request.data.get("version")
    if expected is not None and int(expected) != signing.version:
        return _detail("Contract signing workflow has changed; reload before updating.", status.HTTP_409_CONFLICT)
    previous = signing.state
    target = str(request.data.get("state", signing.state)).upper()
    if target != previous and target not in SIGNING_TRANSITIONS.get(previous, set()):
        return _detail(f"State transition {previous} -> {target} is not allowed.", status.HTTP_409_CONFLICT)
    if "responsibleId" in request.data:
        signing.responsible = organization_user_or_404(request, str(request.data["responsibleId"]), active_only=True) if request.data["responsibleId"] else None
    if "dueAt" in request.data:
        try:
            signing.due_at = _parse_datetime(request.data.get("dueAt"), "dueAt")
        except ValueError as exc:
            return _detail(str(exc))
    if "delayReason" in request.data:
        signing.delay_reason = str(request.data.get("delayReason", "")).strip()
    if target == ContractSigning.State.SIGNED and target != previous:
        return _detail("SIGNED requires verified signature-provider evidence.", status.HTTP_409_CONFLICT)
    if signing.due_at and signing.due_at < timezone.now() and target not in (ContractSigning.State.SIGNED, ContractSigning.State.CANCELLED) and not signing.delay_reason:
        return _detail("delayReason is required when an active signing workflow is overdue.")
    signing.state = target
    signing.version += 1
    signing.save()
    ContractSigningEvent.objects.create(signing=signing, from_state=previous, to_state=target, reason=str(request.data.get("reason", "")).strip(), actor=request.user, metadata={"dueAt": json_value(signing.due_at), "responsibleId": signing.responsible_id})
    return Response(_signing_data(signing))


@api_view(["POST"])
@permission_classes([IsAdmin])
def contract_signature_upload(request, contract_id: str):
    contract = get_object_or_404(Contract.objects, id=contract_id)
    signing = _get_signing(contract)
    if signing.state != ContractSigning.State.SENT_FOR_SIGNATURE:
        return _detail("A final signature file can only be attached after SENT_FOR_SIGNATURE.", status.HTTP_409_CONFLICT)
    uploaded = request.FILES.get("file")
    if uploaded is None:
        return _detail("file is required.")
    suffix = uploaded.name.lower().rsplit(".", 1)[-1] if "." in uploaded.name else ""
    allowed_extensions = {"pdf", "asice"}
    allowed_types = {"application/pdf", "application/vnd.etsi.asic-e+zip", "application/octet-stream"}
    if suffix not in allowed_extensions or uploaded.content_type not in allowed_types:
        return _detail("Only PDF or ASiC-E final documents are allowed.")
    if uploaded.size > 25 * 1024 * 1024:
        return _detail("Signature file exceeds the 25 MB limit.")
    document_sha256 = file_sha256(uploaded)
    previous = signing.state
    signing.final_document = uploaded
    signing.final_url = ""
    signing.final_content_type = uploaded.content_type
    signing.verification_status = ContractSigning.VerificationStatus.PENDING
    signing.document_sha256 = document_sha256
    signing.verified_at = None
    signing.verification_reference = ""
    signing.signer_metadata = {}
    signing.certificate_metadata = {}
    signing.verification_failure_reason = ""
    signing.version += 1
    signing.save()
    ContractSigningEvent.objects.create(signing=signing, from_state=previous, to_state=signing.state, reason=str(request.data.get("reason", "")).strip(), actor=request.user, metadata={"fileName": uploaded.name, "contentType": uploaded.content_type, "size": uploaded.size, "documentSha256": document_sha256, "verificationStatus": signing.verification_status})
    return Response(_signing_data(signing))


@api_view(["POST"])
@permission_classes([IsAdmin])
def contract_signature_verification(request, contract_id: str):
    contract = get_object_or_404(Contract.objects.select_related("source_deal__owner"), id=contract_id)
    signing = _get_signing(contract)
    if signing.state == ContractSigning.State.SIGNED and signing.verification_status == ContractSigning.VerificationStatus.VERIFIED:
        return Response(_signing_data(signing))
    if signing.state != ContractSigning.State.SENT_FOR_SIGNATURE:
        return _detail("Signature evidence can only be accepted after SENT_FOR_SIGNATURE.", status.HTTP_409_CONFLICT)
    payload = request.data if isinstance(request.data, dict) else {}
    try:
        evidence = verify_provider_evidence(
            payload,
            secret=settings.CONTRACT_SIGNATURE_WEBHOOK_SECRET,
            expected_sha256=signing.document_sha256,
            expected_signer_id=contract.source_deal.owner_id if contract.source_deal_id else "",
        )
        if not signing.final_document:
            signed_url = str(payload.get("signedUrl") or "").strip()
            parsed = urlparse(signed_url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise SignatureVerificationError("External signed documents require a secure HTTPS signedUrl.")
            signing.final_url = signed_url
            signing.final_content_type = "application/https-reference"
    except SignatureVerificationError as exc:
        signing.verification_status = ContractSigning.VerificationStatus.FAILED
        signing.verification_failure_reason = str(exc)
        signing.version += 1
        signing.save(update_fields=("verification_status", "verification_failure_reason", "version", "updated_at"))
        ContractSigningEvent.objects.create(signing=signing, from_state=signing.state, to_state=signing.state, reason=str(exc), actor=request.user, metadata={"eventType": "SIGNATURE_VERIFICATION_FAILED", "documentSha256": str(payload.get("documentSha256") or "")})
        return Response(_signing_data(signing), status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    previous = signing.state
    signing.document_sha256 = evidence["documentSha256"]
    signing.verification_status = ContractSigning.VerificationStatus.VERIFIED
    signing.verified_at = timezone.now()
    signing.verification_reference = evidence["providerReference"]
    signing.signer_metadata = evidence["signer"]
    signing.certificate_metadata = evidence["certificate"]
    signing.verification_failure_reason = ""
    signing.state = ContractSigning.State.SIGNED
    signing.version += 1
    signing.save()
    ContractSigningEvent.objects.create(signing=signing, from_state=previous, to_state=signing.state, actor=request.user, metadata={"eventType": "SIGNATURE_VERIFIED", "documentSha256": signing.document_sha256, "providerReference": signing.verification_reference, "verifiedAt": json_value(signing.verified_at)})
    return Response(_signing_data(signing))


def _contract_snapshot(contract: Contract) -> dict:
    deal = contract.source_deal
    offer = contract.source_offer
    if deal is None or offer is None or deal.stage != DealStage.WON or offer.deal_id != deal.id or offer.status != DealOffer.Status.ACCEPTED:
        raise ValueError("Contract source no longer matches a won deal with its accepted offer.")
    return {
        "dealId": str(deal.id),
        "offerId": str(offer.id),
        "acceptedPrice": str(offer.amount),
        "acceptedTerms": offer.terms,
        "seller": {"id": deal.owner_id, "name": deal.owner.name},
        "parcelIds": sorted(str(value) for value in deal.parcels.values_list("id", flat=True)),
        "templateId": str(contract.template_version_id) if contract.template_version_id else None,
        "templateSnapshot": contract.template_snapshot,
    }


def _version_data(version: ContractVersion):
    return {
        "id": str(version.id),
        "contractId": version.contract_id,
        "version": version.version_number,
        "pdfSha256": version.pdf_sha256,
        "snapshot": version.snapshot,
        "checklist": version.checklist,
        "replacement": version.is_replacement,
        "supersedesId": str(version.supersedes_id) if version.supersedes_id else None,
        "changeReason": version.change_reason or None,
        "createdBy": user_data(version.created_by),
        "createdAt": json_value(version.created_at),
    }


@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def contract_versions(request, contract_id: str):
    contract = get_object_or_404(Contract.objects.select_related("source_deal__owner", "source_offer", "template_version"), id=contract_id)
    if request.method == "GET":
        return Response([_version_data(item) for item in contract.controlled_versions.select_related("created_by").all()])
    reason = str(request.data.get("reason", "")).strip()
    checklist = request.data.get("checklist") if isinstance(request.data.get("checklist"), dict) else {}
    if not reason:
        return _detail("reason is required for a replacement contract version.")
    if any(checklist.get(key) is not True for key in CONTRACT_CHECKLIST):
        return _detail(f"checklist must confirm: {', '.join(CONTRACT_CHECKLIST)}.")
    expected = requested_version(request)
    if expected is None:
        return _detail("version is required for optimistic locking.")
    if expected != contract.version:
        return version_conflict_response(contract)
    latest = contract.controlled_versions.order_by("-version_number").first()
    if latest is None:
        return _detail("Initial controlled contract version is missing.", status.HTTP_409_CONFLICT)
    try:
        snapshot = _contract_snapshot(contract)
    except ValueError as exc:
        return _detail(str(exc), status.HTTP_412_PRECONDITION_FAILED)
    for key in ("acceptedPrice", "acceptedTerms", "seller", "parcelIds"):
        if latest.snapshot.get(key) != snapshot.get(key):
            return _detail(f"Current {key} no longer matches the accepted contract basis.", status.HTTP_412_PRECONDITION_FAILED)
    if contract.template_version is None:
        return _detail("The contract has no retained template version.", status.HTTP_412_PRECONDITION_FAILED)
    try:
        html = render_template_preview_html(contract.template_version, contract.source_deal)
        pdf, pdf_sha256 = render_contract_pdf(html=html)
    except (ContractPdfRenderError, ValueError) as exc:
        return _detail(str(exc), status.HTTP_422_UNPROCESSABLE_ENTITY)
    with transaction.atomic():
        locked = Contract.objects.select_for_update().get(id=contract.id)
        if locked.version != expected:
            return version_conflict_response(locked)
        next_number = latest.version_number + 1
        version = ContractVersion.objects.create(
            contract=locked,
            deal=locked.source_deal,
            offer=locked.source_offer,
            version_number=next_number,
            pdf=pdf,
            pdf_sha256=pdf_sha256,
            snapshot=snapshot,
            checklist=checklist,
            is_replacement=True,
            supersedes=latest,
            change_reason=reason,
            created_by=request.user,
        )
        locked.document = pdf
        locked.version += 1
        locked.save(update_fields=("document", "version"))
        history = ContractHistory.objects.filter(id=locked.id).first()
        if history:
            data = dict(history.data or {})
            data["latestControlledVersion"] = {"version": next_number, "pdfSha256": pdf_sha256, "changeReason": reason}
            history.data = data
            history.save(update_fields=("data",))
    return Response(_version_data(version), status=status.HTTP_201_CREATED)


def _quality_data(item: DataQualityIssue):
    return {
        "id": str(item.id),
        "type": item.issue_type,
        "severity": item.severity,
        "status": item.status,
        "owner": owner_summary(item.owner) if item.owner else None,
        "dealId": str(item.deal_id) if item.deal_id else None,
        "description": item.description,
        "evidence": item.evidence,
        "suggestedAssignee": user_data(item.suggested_assignee),
        "assignee": user_data(item.assignee),
        "resolutionNote": item.resolution_note or None,
        "createdAt": json_value(item.created_at),
        "updatedAt": json_value(item.updated_at),
        "events": [
            {"type": event.event_type, "actor": user_data(event.actor), "reason": event.reason or None, "payload": event.payload, "createdAt": json_value(event.created_at)}
            for event in item.events.select_related("actor").all()
        ],
    }


def _fingerprint(issue_type: str, *parts) -> str:
    return hashlib.sha256("|".join([issue_type, *[str(part) for part in parts]]).encode()).hexdigest()


def _quality_upsert(*, issue_type: str, fingerprint: str, severity: str, description: str, owner=None, deal=None, suggested=None, evidence=None):
    existing = DataQualityIssue.objects.filter(fingerprint=fingerprint).first()
    if existing and existing.status == DataQualityIssue.Status.RESOLVED:
        return None, False
    if existing:
        existing.description = description
        existing.severity = severity
        existing.evidence = evidence or {}
        existing.suggested_assignee = suggested
        existing.save(update_fields=("description", "severity", "evidence", "suggested_assignee", "updated_at"))
        return existing, False
    item = DataQualityIssue.objects.create(issue_type=issue_type, fingerprint=fingerprint, severity=severity, description=description, owner=owner, deal=deal, suggested_assignee=suggested, evidence=evidence or {})
    DataQualityIssueEvent.objects.create(issue=item, event_type="CREATED", payload={"source": "P1_SCANNER"})
    return item, True


def _phone_quality_key(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) in (10, 11) and digits.startswith("372"):
        return digits[3:]
    return digits


@api_view(["GET"])
@permission_classes([IsAdmin])
def data_quality_issues(request):
    records = DataQualityIssue.objects.select_related("owner", "owner__assignee", "deal", "suggested_assignee", "assignee").prefetch_related("events__actor")
    for key, field in (("type", "issue_type"), ("severity", "severity"), ("status", "status"), ("assigneeId", "assignee_id")):
        value = str(request.query_params.get(key, "")).strip()
        if value:
            records = records.filter(**{field: value})
    try:
        limit = _limit(request, default=100, maximum=300)
    except ValueError as exc:
        return _detail(str(exc))
    return Response([_quality_data(item) for item in records[:limit]])


@api_view(["POST"])
@permission_classes([IsAdmin])
def data_quality_scan(request):
    created = 0
    seen = 0
    owners = list(Owner.objects.select_related("assignee").all())
    for owner in owners:
        if not owner.phone or not owner.email:
            _, was_created = _quality_upsert(
                issue_type="MISSING_CONTACT",
                fingerprint=_fingerprint("MISSING_CONTACT", owner.id),
                severity=DataQualityIssue.Severity.HIGH if not owner.phone and not owner.email else DataQualityIssue.Severity.MEDIUM,
                description="Owner contact data is incomplete.",
                owner=owner,
                suggested=owner.assignee,
                evidence={"missingPhone": not bool(owner.phone), "missingEmail": not bool(owner.email)},
            )
            seen += 1; created += int(was_created)
        if owner.last_cadastre_list_refresh is None or owner.last_cadastre_list_refresh < timezone.now() - timedelta(days=90):
            _, was_created = _quality_upsert(
                issue_type="STALE_OWNER_DATA",
                fingerprint=_fingerprint("STALE_OWNER_DATA", owner.id),
                severity=DataQualityIssue.Severity.MEDIUM,
                description="Owner registry/portfolio data has not been refreshed within 90 days.",
                owner=owner,
                suggested=owner.assignee,
                evidence={"lastCadastreListRefresh": json_value(owner.last_cadastre_list_refresh)},
            )
            seen += 1; created += int(was_created)
    phone_groups = defaultdict(list)
    email_groups = defaultdict(list)
    for owner in owners:
        phone = _phone_quality_key(owner.phone)
        email = (owner.email or "").strip().lower()
        if phone:
            phone_groups[phone].append(owner)
        if email:
            email_groups[email].append(owner)
    for kind, groups in (("DUPLICATE_PHONE", phone_groups), ("DUPLICATE_EMAIL", email_groups)):
        for value, members in groups.items():
            if len(members) < 2:
                continue
            ids = sorted(owner.id for owner in members)
            _, was_created = _quality_upsert(
                issue_type=kind,
                fingerprint=_fingerprint(kind, *ids),
                severity=DataQualityIssue.Severity.HIGH,
                description=f"Possible duplicate owners share the same {'phone' if kind.endswith('PHONE') else 'email'}.",
                suggested=members[0].assignee,
                evidence={"value": value, "ownerIds": ids, "manualReviewRequired": True},
            )
            seen += 1; created += int(was_created)
    active_deals = Deal.objects.select_related("owner", "owner__assignee", "evaluator", "created_by").exclude(stage__in=CLOSED_DEAL_STAGES)
    for deal in active_deals:
        suggested = deal.evaluator or deal.owner.assignee or deal.created_by
        has_action = deal.next_actions.filter(status__in=[NextAction.Status.OPEN, NextAction.Status.POSTPONED]).exists()
        if not has_action:
            _, was_created = _quality_upsert(
                issue_type="DEAL_NO_NEXT_ACTION",
                fingerprint=_fingerprint("DEAL_NO_NEXT_ACTION", deal.id),
                severity=DataQualityIssue.Severity.HIGH,
                description="Active deal has no open next action.",
                owner=deal.owner,
                deal=deal,
                suggested=suggested,
                evidence={"stage": deal.stage},
            )
            seen += 1; created += int(was_created)
        if deal.stage == DealStage.EVALUATION:
            try:
                due_at = deal.work_state.evaluation_due_at
            except DealWorkState.DoesNotExist:
                due_at = None
            if due_at is None:
                _, was_created = _quality_upsert(
                    issue_type="EVALUATION_DEADLINE_MISSING",
                    fingerprint=_fingerprint("EVALUATION_DEADLINE_MISSING", deal.id),
                    severity=DataQualityIssue.Severity.HIGH,
                    description="Evaluation-stage deal has no evaluation deadline.",
                    owner=deal.owner,
                    deal=deal,
                    suggested=suggested,
                    evidence={"stage": deal.stage},
                )
                seen += 1; created += int(was_created)
    return Response({"detected": seen, "created": created, "queueSize": DataQualityIssue.objects.exclude(status=DataQualityIssue.Status.RESOLVED).count()})


@api_view(["PATCH"])
@permission_classes([IsAdmin])
def data_quality_issue_detail(request, issue_id):
    item = get_object_or_404(DataQualityIssue.objects.select_related("owner", "deal", "suggested_assignee", "assignee"), id=issue_id)
    operation = str(request.data.get("operation", "")).upper()
    reason = str(request.data.get("reason", "")).strip()
    if operation == "ASSIGN":
        assignee = organization_user_or_404(request, str(request.data.get("assigneeId", "")), active_only=True)
        item.assignee = assignee
        item.status = DataQualityIssue.Status.ASSIGNED
        item.resolved_at = None
    elif operation == "RELEASE":
        item.assignee = None
        item.status = DataQualityIssue.Status.OPEN
        item.resolved_at = None
    elif operation == "RESOLVE":
        if not reason:
            return _detail("reason is required when resolving a data-quality issue.")
        item.status = DataQualityIssue.Status.RESOLVED
        item.resolution_note = reason
        item.resolved_at = timezone.now()
    else:
        return _detail("operation must be ASSIGN, RELEASE or RESOLVE.")
    item.save()
    DataQualityIssueEvent.objects.create(issue=item, event_type=operation, actor=request.user, reason=reason, payload={"assigneeId": item.assignee_id})
    return Response(_quality_data(item))


def _relation_data(item: OwnershipRelation):
    return {
        "id": str(item.id),
        "owner": owner_summary(item.owner),
        "cadastre": {"id": item.cadastre_id, "name": item.cadastre.name or None, "area": json_value(item.cadastre.area)},
        "source": item.source,
        "sourceReference": item.source_reference or None,
        "validFrom": json_value(item.valid_from),
        "validTo": json_value(item.valid_to),
        "endedReason": item.ended_reason or None,
        "protected": item.manual_protected,
        "active": item.is_active,
        "events": [
            {"type": event.event_type, "actor": user_data(event.actor), "reason": event.reason or None, "payload": event.payload, "createdAt": json_value(event.created_at)}
            for event in item.events.select_related("actor").all()
        ],
    }


def _project_legacy_relations(owner: Owner):
    tracked = set(OwnershipRelation.objects.filter(owner=owner, is_active=True).values_list("cadastre_id", flat=True))
    for legacy in OwnerCadastre.objects.filter(owner=owner).select_related("cadastre"):
        if legacy.cadastre_id in tracked:
            continue
        blocked = OwnershipRelation.objects.filter(owner=owner, cadastre_id=legacy.cadastre_id, is_active=False, manual_protected=True).exists()
        if blocked:
            legacy.delete()
            continue
        relation = OwnershipRelation.objects.create(owner=owner, cadastre=legacy.cadastre, source=OwnershipRelation.Source.LEGACY, source_reference="BACKFILLED_OWNER_CADASTRE")
        OwnershipRelationEvent.objects.create(relation=relation, event_type="LEGACY_BACKFILLED", payload={"legacyRelationId": legacy.pk})


@api_view(["GET", "POST"])
@permission_classes([CanManageOwners])
def owner_relations(request, owner_id: str):
    owner, denied = _owner_or_403(request, owner_id)
    if denied:
        return denied
    _project_legacy_relations(owner)
    if request.method == "GET":
        try:
            cursor = _decode_cursor(request.query_params.get("cursor"))
            limit = _limit(request)
        except ValueError as exc:
            return _detail(str(exc))
        records = OwnershipRelation.objects.filter(owner=owner).select_related("owner", "owner__assignee", "cadastre").prefetch_related("events__actor").order_by("id")
        active = request.query_params.get("active")
        if active in ("true", "false"):
            records = records.filter(is_active=active == "true")
        if cursor:
            records = records.filter(id__gt=cursor)
        page = list(records[: limit + 1])
        has_more = len(page) > limit
        page = page[:limit]
        return Response({"items": [_relation_data(item) for item in page], "nextCursor": _encode_cursor(str(page[-1].id)) if has_more and page else None, "pageSize": limit})
    cadastre_id = str(request.data.get("cadastreId", "")).strip()
    if not cadastre_id:
        return _detail("cadastreId is required.")
    cadastre = get_object_or_404(Cadastre, id=cadastre_id)
    with transaction.atomic():
        active = OwnershipRelation.objects.filter(owner=owner, cadastre=cadastre, is_active=True).first()
        if active:
            return _detail("An active owner-cadastre relation already exists.", status.HTTP_409_CONFLICT)
        relation = OwnershipRelation.objects.filter(owner=owner, cadastre=cadastre, is_active=False).order_by("-valid_to").first()
        if relation:
            relation.is_active = True
            relation.valid_to = None
            relation.ended_reason = ""
            relation.source = OwnershipRelation.Source.MANUAL
            relation.manual_protected = True
            relation.updated_by = request.user
            relation.save()
            event_type = "MANUAL_REACTIVATED"
        else:
            relation = OwnershipRelation.objects.create(owner=owner, cadastre=cadastre, source=OwnershipRelation.Source.MANUAL, source_reference=str(request.data.get("sourceReference", "")).strip(), manual_protected=bool(request.data.get("protected", True)), created_by=request.user, updated_by=request.user)
            event_type = "MANUAL_CREATED"
        OwnerCadastre.objects.get_or_create(owner=owner, cadastre=cadastre)
        OwnershipRelationEvent.objects.create(relation=relation, event_type=event_type, actor=request.user, reason=str(request.data.get("reason", "")).strip())
    return Response(_relation_data(relation), status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([CanManageOwners])
def ownership_relation_detail(request, relation_id):
    relation = get_object_or_404(OwnershipRelation.objects.select_related("owner", "owner__assignee", "cadastre").prefetch_related("events__actor"), id=relation_id)
    if not can_access_owner(request, relation.owner):
        return _detail("You do not have access to this ownership relation.", status.HTTP_403_FORBIDDEN)
    operation = str(request.data.get("operation", "")).upper()
    reason = str(request.data.get("reason", "")).strip()
    with transaction.atomic():
        if operation == "END":
            if not relation.is_active:
                return _detail("Relation is already inactive.", status.HTTP_409_CONFLICT)
            if not reason:
                return _detail("reason is required when ending a relation.")
            relation.is_active = False
            relation.valid_to = timezone.now()
            relation.ended_reason = reason
            relation.manual_protected = bool(request.data.get("protected", True))
            relation.updated_by = request.user
            relation.save()
            OwnerCadastre.objects.filter(owner=relation.owner, cadastre=relation.cadastre).delete()
            event_type = "ENDED"
        elif operation == "REACTIVATE":
            if OwnershipRelation.objects.filter(owner=relation.owner, cadastre=relation.cadastre, is_active=True).exclude(id=relation.id).exists():
                return _detail("Another active relation already exists.", status.HTTP_409_CONFLICT)
            relation.is_active = True
            relation.valid_to = None
            relation.ended_reason = ""
            relation.manual_protected = True
            relation.source = OwnershipRelation.Source.MANUAL
            relation.updated_by = request.user
            relation.save()
            OwnerCadastre.objects.get_or_create(owner=relation.owner, cadastre=relation.cadastre)
            event_type = "REACTIVATED"
        elif operation == "RESOLVE_CONFLICT":
            resolution = str(request.data.get("resolution", "")).upper()
            if not reason or resolution not in ("KEEP_MANUAL", "ACCEPT_EXTERNAL"):
                return _detail("RESOLVE_CONFLICT requires reason and resolution KEEP_MANUAL or ACCEPT_EXTERNAL.")
            if resolution == "ACCEPT_EXTERNAL":
                relation.manual_protected = False
                relation.is_active = True
                relation.valid_to = None
                relation.ended_reason = ""
                relation.source = OwnershipRelation.Source.EXTERNAL
                OwnerCadastre.objects.get_or_create(owner=relation.owner, cadastre=relation.cadastre)
            else:
                relation.manual_protected = True
                if not relation.is_active:
                    OwnerCadastre.objects.filter(owner=relation.owner, cadastre=relation.cadastre).delete()
            relation.updated_by = request.user
            relation.save()
            event_type = "CONFLICT_RESOLVED"
        else:
            return _detail("operation must be END, REACTIVATE or RESOLVE_CONFLICT.")
        OwnershipRelationEvent.objects.create(relation=relation, event_type=event_type, actor=request.user, reason=reason, payload={"operation": operation, "resolution": request.data.get("resolution")})
    return Response(_relation_data(relation))
