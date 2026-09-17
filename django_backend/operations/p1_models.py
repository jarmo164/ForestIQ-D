"""P1 workflow models for sales, contracts, data quality and ownership lifecycle."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from accounts.models import OrganizationScopedModel


class ContactActivity(OrganizationScopedModel):
    class Channel(models.TextChoices):
        PHONE = "PHONE", "Phone"
        EMAIL = "EMAIL", "Email"
        MEETING = "MEETING", "Meeting"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey("forestry.Owner", on_delete=models.CASCADE, related_name="contact_activities")
    deal = models.ForeignKey("operations.Deal", null=True, blank=True, on_delete=models.SET_NULL, related_name="contact_activities")
    channel = models.CharField(max_length=20, choices=Channel.choices)
    outcome_code = models.CharField(max_length=80)
    outcome_reason = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_contact_activities")
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("owner", "deal")

    class Meta:
        db_table = "p1_contact_activities"
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("organization", "owner", "created_at"), name="p1_contact_owner_time_idx")]


class DealWorkState(OrganizationScopedModel):
    deal = models.OneToOneField("operations.Deal", on_delete=models.CASCADE, primary_key=True, related_name="work_state")
    evaluation_due_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    organization_parent_fields = ("deal",)

    class Meta:
        db_table = "p1_deal_work_state"


class NextAction(OrganizationScopedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        DONE = "DONE", "Done"
        POSTPONED = "POSTPONED", "Postponed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey("forestry.Owner", on_delete=models.CASCADE, related_name="next_actions")
    deal = models.ForeignKey("operations.Deal", null=True, blank=True, on_delete=models.CASCADE, related_name="next_actions")
    source_activity = models.ForeignKey(ContactActivity, null=True, blank=True, on_delete=models.SET_NULL, related_name="next_actions")
    text = models.CharField(max_length=500)
    due_at = models.DateTimeField()
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assigned_next_actions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_next_actions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    organization_parent_fields = ("owner", "deal", "source_activity")

    class Meta:
        db_table = "p1_next_actions"
        ordering = ("due_at", "id")
        indexes = [
            models.Index(fields=("organization", "status", "due_at"), name="p1_action_status_due_idx"),
            models.Index(fields=("organization", "assignee", "status"), name="p1_action_assignee_idx"),
        ]


class WorkflowAuditEvent(OrganizationScopedModel):
    id = models.BigAutoField(primary_key=True)
    owner = models.ForeignKey("forestry.Owner", null=True, blank=True, on_delete=models.CASCADE, related_name="workflow_events")
    deal = models.ForeignKey("operations.Deal", null=True, blank=True, on_delete=models.CASCADE, related_name="workflow_events")
    activity = models.ForeignKey(ContactActivity, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events")
    next_action = models.ForeignKey(NextAction, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events")
    event_type = models.CharField(max_length=80)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="workflow_audit_events")
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("owner", "deal", "activity", "next_action")

    class Meta:
        db_table = "p1_workflow_audit"
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("organization", "owner", "created_at"), name="p1_workflow_owner_idx")]


class LossReasonCode(OrganizationScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50)
    label = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "p1_loss_reason_codes"
        ordering = ("sort_order", "label", "code")
        constraints = [models.UniqueConstraint(fields=("organization", "code"), name="p1_uq_loss_reason_code")]


class DealLossOutcome(OrganizationScopedModel):
    deal = models.OneToOneField("operations.Deal", on_delete=models.CASCADE, primary_key=True, related_name="structured_loss")
    reason = models.ForeignKey(LossReasonCode, on_delete=models.PROTECT, related_name="deal_outcomes")
    previous_stage = models.CharField(max_length=40)
    note = models.TextField(blank=True)
    follow_up_at = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="recorded_deal_losses")
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("deal", "reason")

    class Meta:
        db_table = "p1_deal_loss_outcomes"
        indexes = [models.Index(fields=("organization", "created_at"), name="p1_loss_created_idx")]


class DecisionEvidenceSnapshot(OrganizationScopedModel):
    class DecisionType(models.TextChoices):
        EVALUATION = "EVALUATION", "Evaluation"
        OFFER = "OFFER", "Offer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.ForeignKey("operations.Deal", on_delete=models.PROTECT, related_name="decision_evidence_snapshots")
    sequence = models.PositiveIntegerField()
    decision_type = models.CharField(max_length=20, choices=DecisionType.choices, default=DecisionType.EVALUATION)
    schema_version = models.PositiveSmallIntegerField(default=1)
    snapshot = models.JSONField(default=dict)
    snapshot_sha256 = models.CharField(max_length=64)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="confirmed_decision_evidence_snapshots")
    confirmed_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("deal",)

    class Meta:
        db_table = "p2_decision_evidence_snapshots"
        ordering = ("deal_id", "-sequence")
        constraints = [models.UniqueConstraint(fields=("organization", "deal", "sequence"), name="p2_uq_decision_snapshot_sequence")]
        indexes = [models.Index(fields=("organization", "deal", "confirmed_at"), name="p2_decision_snapshot_deal_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Decision evidence snapshots are immutable.")
        return super().save(*args, **kwargs)


class MapWorkbasket(OrganizationScopedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        CANCELLED = "CANCELLED", "Cancelled"

    class Permission(models.TextChoices):
        VIEW = "VIEW", "View"
        EDIT = "EDIT", "Edit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    purpose = models.CharField(max_length=500, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    permission = models.CharField(max_length=10, choices=Permission.choices, default=Permission.VIEW)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_map_workbaskets")
    assigned_to_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="assigned_map_workbaskets")
    assigned_to_role = models.CharField(max_length=80, blank=True)
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="accepted_map_workbaskets")
    accepted_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "p2_map_workbaskets"
        ordering = ("-updated_at", "-created_at", "name")
        indexes = [
            models.Index(fields=("organization", "created_by", "status"), name="p2_workbasket_creator_idx"),
            models.Index(fields=("organization", "assigned_to_user", "status"), name="p2_workbasket_user_idx"),
            models.Index(fields=("organization", "assigned_to_role", "status"), name="p2_workbasket_role_idx"),
        ]


class MapWorkbasketItem(OrganizationScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    basket = models.ForeignKey(MapWorkbasket, on_delete=models.CASCADE, related_name="items")
    cadastre = models.ForeignKey("forestry.Cadastre", on_delete=models.PROTECT, related_name="map_workbasket_items")
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="added_map_workbasket_items")
    added_at = models.DateTimeField(auto_now_add=True)
    sort_order = models.PositiveIntegerField(default=0)
    organization_parent_fields = ("basket", "cadastre")

    class Meta:
        db_table = "p2_map_workbasket_items"
        ordering = ("sort_order", "added_at", "id")
        constraints = [models.UniqueConstraint(fields=("organization", "basket", "cadastre"), name="p2_uq_workbasket_cadastre")]
        indexes = [models.Index(fields=("organization", "cadastre"), name="p2_workbasket_cadastre_idx")]


class ContractSigning(OrganizationScopedModel):
    class State(models.TextChoices):
        PREPARING = "PREPARING", "Preparing"
        SENT_FOR_SIGNATURE = "SENT_FOR_SIGNATURE", "Sent for signature"
        SIGNED = "SIGNED", "Signed"
        CANCELLED = "CANCELLED", "Cancelled"

    contract = models.OneToOneField("operations.Contract", on_delete=models.CASCADE, primary_key=True, related_name="signing")
    state = models.CharField(max_length=30, choices=State.choices, default=State.PREPARING)
    responsible = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="responsible_contract_signings")
    due_at = models.DateTimeField(null=True, blank=True)
    delay_reason = models.TextField(blank=True)
    final_document = models.FileField(upload_to="contract-signatures/%Y/%m", null=True, blank=True)
    final_url = models.URLField(max_length=1000, blank=True)
    final_content_type = models.CharField(max_length=120, blank=True)
    version = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    organization_parent_fields = ("contract",)

    class Meta:
        db_table = "p1_contract_signing"


class ContractSigningEvent(OrganizationScopedModel):
    id = models.BigAutoField(primary_key=True)
    signing = models.ForeignKey(ContractSigning, on_delete=models.CASCADE, related_name="events")
    from_state = models.CharField(max_length=30, blank=True)
    to_state = models.CharField(max_length=30)
    reason = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="contract_signing_events")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("signing",)

    class Meta:
        db_table = "p1_contract_signing_events"
        ordering = ("created_at", "id")


class ContractVersion(OrganizationScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract = models.ForeignKey("operations.Contract", on_delete=models.CASCADE, related_name="controlled_versions")
    deal = models.ForeignKey("operations.Deal", on_delete=models.PROTECT, related_name="contract_versions")
    offer = models.ForeignKey("operations.DealOffer", on_delete=models.PROTECT, related_name="contract_versions")
    version_number = models.PositiveIntegerField()
    pdf = models.BinaryField()
    pdf_sha256 = models.CharField(max_length=64)
    snapshot = models.JSONField(default=dict)
    checklist = models.JSONField(default=dict)
    is_replacement = models.BooleanField(default=False)
    supersedes = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="replacements")
    change_reason = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_contract_versions")
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("contract", "deal", "offer", "supersedes")

    class Meta:
        db_table = "p1_contract_versions"
        ordering = ("contract_id", "version_number")
        constraints = [models.UniqueConstraint(fields=("organization", "contract", "version_number"), name="p1_uq_contract_version")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Controlled contract versions are immutable.")
        return super().save(*args, **kwargs)


class DataQualityIssue(OrganizationScopedModel):
    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ASSIGNED = "ASSIGNED", "Assigned"
        RESOLVED = "RESOLVED", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue_type = models.CharField(max_length=80)
    fingerprint = models.CharField(max_length=64)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    owner = models.ForeignKey("forestry.Owner", null=True, blank=True, on_delete=models.CASCADE, related_name="quality_issues")
    deal = models.ForeignKey("operations.Deal", null=True, blank=True, on_delete=models.CASCADE, related_name="quality_issues")
    description = models.TextField()
    evidence = models.JSONField(default=dict, blank=True)
    suggested_assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="suggested_quality_issues")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_quality_issues")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    organization_parent_fields = ("owner", "deal")

    class Meta:
        db_table = "p1_data_quality_issues"
        ordering = ("-created_at", "id")
        constraints = [models.UniqueConstraint(fields=("organization", "fingerprint"), name="p1_uq_quality_fingerprint")]
        indexes = [models.Index(fields=("organization", "status", "severity"), name="p1_quality_queue_idx")]


class DataQualityIssueEvent(OrganizationScopedModel):
    id = models.BigAutoField(primary_key=True)
    issue = models.ForeignKey(DataQualityIssue, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=50)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="quality_issue_events")
    reason = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("issue",)

    class Meta:
        db_table = "p1_data_quality_events"
        ordering = ("created_at", "id")


class OwnershipRelation(OrganizationScopedModel):
    class Source(models.TextChoices):
        LEGACY = "LEGACY", "Legacy"
        EXTERNAL = "EXTERNAL", "External"
        MANUAL = "MANUAL", "Manual"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey("forestry.Owner", on_delete=models.CASCADE, related_name="ownership_relations")
    cadastre = models.ForeignKey("forestry.Cadastre", on_delete=models.CASCADE, related_name="ownership_relations")
    source = models.CharField(max_length=30, choices=Source.choices, default=Source.EXTERNAL)
    source_reference = models.CharField(max_length=255, blank=True)
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    ended_reason = models.TextField(blank=True)
    manual_protected = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_ownership_relations")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="updated_ownership_relations")
    updated_at = models.DateTimeField(auto_now=True)
    organization_parent_fields = ("owner", "cadastre")

    class Meta:
        db_table = "p1_ownership_relations"
        ordering = ("-is_active", "owner_id", "cadastre_id", "-valid_from")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "owner", "cadastre"),
                condition=Q(is_active=True),
                name="p1_uq_active_owner_cad",
            )
        ]
        indexes = [models.Index(fields=("organization", "owner", "is_active"), name="p1_relation_owner_idx")]


class OwnershipRelationEvent(OrganizationScopedModel):
    id = models.BigAutoField(primary_key=True)
    relation = models.ForeignKey(OwnershipRelation, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=80)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="ownership_relation_events")
    reason = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("relation",)

    class Meta:
        db_table = "p1_ownership_relation_events"
        ordering = ("created_at", "id")
