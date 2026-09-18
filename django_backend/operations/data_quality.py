"""Chunked, auditable data-quality scanner shared by HTTP and Celery."""
from __future__ import annotations

import hashlib
from datetime import timedelta
from typing import Iterable

from django.db.models import Case, CharField, Count, F, Func, Value, When
from django.db.models.functions import Length, Lower, Substr, Trim
from django.utils import timezone

from forestry.models import Owner
from operations.models import Deal, DealStage
from operations.p1_models import DataQualityIssue, DataQualityIssueEvent, DataQualityScanRun, DealWorkState, NextAction


CLOSED_DEAL_STAGES = (DealStage.WON, DealStage.LOST, DealStage.CANCELLED)


def _fingerprint(*parts) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()


def _upsert(*, issue_type: str, fingerprint: str, severity: str, description: str, owner=None, deal=None, suggested=None, evidence=None):
    existing = DataQualityIssue.objects.filter(fingerprint=fingerprint).first()
    if existing and existing.status == DataQualityIssue.Status.RESOLVED:
        return existing, False
    if existing:
        existing.description = description
        existing.severity = severity
        existing.evidence = evidence or {}
        existing.suggested_assignee = suggested
        existing.save(update_fields=("description", "severity", "evidence", "suggested_assignee", "updated_at"))
        return existing, False
    item = DataQualityIssue.objects.create(
        issue_type=issue_type, fingerprint=fingerprint, severity=severity, description=description,
        owner=owner, deal=deal, suggested_assignee=suggested, evidence=evidence or {},
    )
    DataQualityIssueEvent.objects.create(issue=item, event_type="CREATED", payload={"source": "P1_SCANNER"})
    return item, True


def _auto_resolve(fingerprint: str, *, reason: str) -> int:
    item = DataQualityIssue.objects.filter(fingerprint=fingerprint).exclude(status=DataQualityIssue.Status.RESOLVED).first()
    if item is None:
        return 0
    item.status = DataQualityIssue.Status.RESOLVED
    item.resolution_note = reason
    item.resolved_at = timezone.now()
    item.save(update_fields=("status", "resolution_note", "resolved_at", "updated_at"))
    DataQualityIssueEvent.objects.create(issue=item, event_type="AUTO_RESOLVED", reason=reason, payload={"source": "P1_SCANNER"})
    return 1


def _phone_annotations(queryset):
    """Normalize phones exactly like the legacy Python scanner, but in PostgreSQL."""

    compact = Func(
        F("phone"),
        Value(r"\D"),
        Value(""),
        Value("g"),
        function="REGEXP_REPLACE",
        output_field=CharField(),
    )
    queryset = queryset.annotate(_phone_compact=compact).annotate(_phone_length=Length("_phone_compact"))
    return queryset.annotate(
        _quality_key=Case(
            When(_phone_compact__startswith="372", _phone_length__in=(10, 11), then=Substr("_phone_compact", 4)),
            default=F("_phone_compact"),
            output_field=CharField(),
        )
    )


def _duplicate_groups(kind: str) -> Iterable[tuple[str, list[Owner]]]:
    if kind == "DUPLICATE_PHONE":
        query = _phone_annotations(Owner.objects.exclude(phone="")).exclude(_quality_key="")
        groups = query.values("_quality_key").annotate(total=Count("id")).filter(total__gt=1).iterator(chunk_size=200)
        for group in groups:
            key = group["_quality_key"]
            members = list(_phone_annotations(Owner.objects.select_related("assignee")).filter(_quality_key=key).order_by("id")[:100])
            yield key, members
        return
    query = Owner.objects.exclude(email="").annotate(_quality_key=Lower(Trim("email"))).exclude(_quality_key="")
    groups = query.values("_quality_key").annotate(total=Count("id")).filter(total__gt=1).iterator(chunk_size=200)
    for group in groups:
        key = group["_quality_key"]
        members = list(Owner.objects.select_related("assignee").annotate(_quality_key=Lower(Trim("email"))).filter(_quality_key=key).order_by("id")[:100])
        yield key, members


def run_data_quality_scan(*, trigger: str = "MANUAL", batch_size: int = 250) -> DataQualityScanRun:
    run = DataQualityScanRun.objects.create(status=DataQualityScanRun.Status.RUNNING, trigger=trigger)
    detected = created = auto_resolved = owners_processed = deals_processed = 0
    now = timezone.now()
    duplicate_fingerprints: set[str] = set()
    try:
        owners = Owner.objects.select_related("assignee").order_by("id")
        for owner in owners.iterator(chunk_size=batch_size):
            owners_processed += 1
            missing_fp = _fingerprint("MISSING_CONTACT", owner.id)
            if not owner.phone or not owner.email:
                _, was_created = _upsert(
                    issue_type="MISSING_CONTACT", fingerprint=missing_fp,
                    severity=DataQualityIssue.Severity.HIGH if not owner.phone and not owner.email else DataQualityIssue.Severity.MEDIUM,
                    description="Owner contact data is incomplete.", owner=owner, suggested=owner.assignee,
                    evidence={"missingPhone": not bool(owner.phone), "missingEmail": not bool(owner.email)},
                )
                detected += 1; created += int(was_created)
            else:
                auto_resolved += _auto_resolve(missing_fp, reason="Owner contact data is complete.")

            stale_fp = _fingerprint("STALE_OWNER_DATA", owner.id)
            if owner.last_cadastre_list_refresh is None or owner.last_cadastre_list_refresh < now - timedelta(days=90):
                _, was_created = _upsert(
                    issue_type="STALE_OWNER_DATA", fingerprint=stale_fp, severity=DataQualityIssue.Severity.MEDIUM,
                    description="Owner registry/portfolio data has not been refreshed within 90 days.", owner=owner, suggested=owner.assignee,
                    evidence={"lastCadastreListRefresh": owner.last_cadastre_list_refresh.isoformat() if owner.last_cadastre_list_refresh else None},
                )
                detected += 1; created += int(was_created)
            else:
                auto_resolved += _auto_resolve(stale_fp, reason="Owner registry data is fresh again.")

        for kind in ("DUPLICATE_PHONE", "DUPLICATE_EMAIL"):
            for value, members in _duplicate_groups(kind):
                if len(members) < 2:
                    continue
                ids = sorted(owner.id for owner in members)
                fingerprint = _fingerprint(kind, *ids)
                duplicate_fingerprints.add(fingerprint)
                _, was_created = _upsert(
                    issue_type=kind, fingerprint=fingerprint, severity=DataQualityIssue.Severity.HIGH,
                    description=f"Possible duplicate owners share the same {'phone' if kind.endswith('PHONE') else 'email'}.",
                    suggested=members[0].assignee,
                    evidence={"value": value, "ownerIds": ids, "manualReviewRequired": True},
                )
                detected += 1; created += int(was_created)

        for old in DataQualityIssue.objects.filter(issue_type__in=("DUPLICATE_PHONE", "DUPLICATE_EMAIL")).exclude(status=DataQualityIssue.Status.RESOLVED).only("fingerprint"):
            if old.fingerprint not in duplicate_fingerprints:
                auto_resolved += _auto_resolve(old.fingerprint, reason="The duplicate signal is no longer present.")

        deals = Deal.objects.select_related("owner", "owner__assignee", "evaluator", "created_by").exclude(stage__in=CLOSED_DEAL_STAGES).order_by("id")
        for deal in deals.iterator(chunk_size=batch_size):
            deals_processed += 1
            suggested = deal.evaluator or deal.owner.assignee or deal.created_by
            action_fp = _fingerprint("DEAL_NO_NEXT_ACTION", deal.id)
            has_action = deal.next_actions.filter(status__in=[NextAction.Status.OPEN, NextAction.Status.POSTPONED]).exists()
            if not has_action:
                _, was_created = _upsert(
                    issue_type="DEAL_NO_NEXT_ACTION", fingerprint=action_fp, severity=DataQualityIssue.Severity.HIGH,
                    description="Active deal has no open next action.", owner=deal.owner, deal=deal, suggested=suggested, evidence={"stage": deal.stage},
                )
                detected += 1; created += int(was_created)
            else:
                auto_resolved += _auto_resolve(action_fp, reason="The deal has an open next action.")

            evaluation_fp = _fingerprint("EVALUATION_DEADLINE_MISSING", deal.id)
            due_at = None
            if deal.stage == DealStage.EVALUATION:
                try:
                    due_at = deal.work_state.evaluation_due_at
                except DealWorkState.DoesNotExist:
                    pass
            if deal.stage == DealStage.EVALUATION and due_at is None:
                _, was_created = _upsert(
                    issue_type="EVALUATION_DEADLINE_MISSING", fingerprint=evaluation_fp, severity=DataQualityIssue.Severity.HIGH,
                    description="Evaluation-stage deal has no evaluation deadline.", owner=deal.owner, deal=deal, suggested=suggested, evidence={"stage": deal.stage},
                )
                detected += 1; created += int(was_created)
            else:
                auto_resolved += _auto_resolve(evaluation_fp, reason="The evaluation deadline requirement is satisfied.")

        run.status = DataQualityScanRun.Status.SUCCESS
        run.detected_count = detected
        run.created_count = created
        run.auto_resolved_count = auto_resolved
        run.processed_owner_count = owners_processed
        run.processed_deal_count = deals_processed
        run.finished_at = timezone.now()
        run.save()
        return run
    except Exception as exc:
        run.status = DataQualityScanRun.Status.FAILED
        run.detected_count = detected
        run.created_count = created
        run.auto_resolved_count = auto_resolved
        run.processed_owner_count = owners_processed
        run.processed_deal_count = deals_processed
        run.error_message = str(exc)[:4000]
        run.finished_at = timezone.now()
        run.save()
        raise
