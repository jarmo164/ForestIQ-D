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

from django.db import transaction
from django.db.models import DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import PrivilegeCode
from forestry.models import Cadastre, Owner, OwnerCadastre, OwnerLog
from operations.models import Contract, ContractHistory, Deal, DealOffer, DealStage
from operations.p1_models import (
    ContactActivity,
    ContractSigning,
    ContractSigningEvent,
    ContractVersion,
    DataQualityIssue,
    DataQualityIssueEvent,
    DealLossOutcome,
    DealWorkState,
    LossReasonCode,
    NextAction,
    OwnershipRelation,
    OwnershipRelationEvent,
    WorkflowAuditEvent,
)
from operations.services.contract_pdf import ContractPdfRenderError, render_contract_pdf

from .concurrency import requested_version, version_conflict_response
from .contract_templates import render_template_preview_html
from .organization import organization_user_or_404, request_organization_id
from .parity import _commercial, _get_deal, _update_deal_or_conflict
from .permissions import CanManageOwners, IsAdmin, can_access_deal, can_access_owner, has_membership_privilege
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
    return WorkflowAuditEvent.objects.create(
        owner=owner,
        deal=deal,
        activity=activity,
        next_action=next_action,
        actor=actor,
        event_type=event_type,
        payload=payload or {},
    )


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
    signed_url = str(request.data.get("signedUrl", signing.final_url or "")).strip()
    if target == ContractSigning.State.SIGNED and target != previous:
        parsed = urlparse(signed_url)
        if not signing.final_document and (parsed.scheme != "https" or not parsed.netloc):
            return _detail("SIGNED requires an uploaded PDF/ASiC-E file or a secure HTTPS signedUrl.")
        signing.final_url = signed_url
        signing.final_content_type = signing.final_content_type or "application/https-reference"
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
    previous = signing.state
    signing.final_document = uploaded
    signing.final_url = ""
    signing.final_content_type = uploaded.content_type
    signing.state = ContractSigning.State.SIGNED
    signing.version += 1
    signing.save()
    ContractSigningEvent.objects.create(signing=signing, from_state=previous, to_state=signing.state, reason=str(request.data.get("reason", "")).strip(), actor=request.user, metadata={"fileName": uploaded.name, "contentType": uploaded.content_type, "size": uploaded.size})
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
        phone = re.sub(r"\D", "", owner.phone or "")
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
