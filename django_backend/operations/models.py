"""Operational workflow models: reminders, messages, contracts and contact data."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from accounts.models import OrganizationScopedModel
from forestry.models import Owner


class Reminder(OrganizationScopedModel):
    due_time = models.DateTimeField(db_column="duetime")
    text = models.TextField(blank=True, db_column="reminder_text")
    owner = models.ForeignKey(Owner, null=True, blank=True, on_delete=models.CASCADE, related_name="reminders", db_column="owner_id")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_reminders",
        db_column="creator",
    )
    created_time = models.DateTimeField(auto_now_add=True, db_column="created_time")
    cadastre = models.TextField(blank=True)
    property_name = models.TextField(blank=True)
    organization_parent_fields = ("owner", "creator")

    class Meta:
        db_table = "reminders"
        ordering = ("due_time", "id")
        indexes = [models.Index(fields=("organization", "due_time"), name="reminder_organization_due_idx")]


class ApplicationMessage(OrganizationScopedModel):
    text = models.TextField(db_column="message_text")
    admin_message = models.BooleanField(default=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="application_messages",
        db_column="recipient",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("recipient",)

    class Meta:
        db_table = "application_messages"
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("organization", "recipient", "created_at"), name="app_message_org_idx")]


class DirectMessage(OrganizationScopedModel):
    text = models.TextField(db_column="message")
    created_at = models.DateTimeField(auto_now_add=True)
    noticed_at = models.DateTimeField(null=True, blank=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_direct_messages",
        db_column="sender",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="received_direct_messages",
        db_column="recipient",
    )
    organization_parent_fields = ("recipient", "sender")

    class Meta:
        db_table = "messages"
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("organization", "recipient", "noticed_at"), name="message_org_received_idx"),
            models.Index(fields=("organization", "sender", "created_at"), name="message_organization_sent_idx"),
        ]


class PersonDump(OrganizationScopedModel):
    source = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=500, blank=True)
    code = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "persons_dump"
        ordering = ("name", "id")


class CompanyProfile(OrganizationScopedModel):
    """Legal entity data selected when drafting a contract."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_name = models.CharField(max_length=255)
    registry_code = models.CharField(max_length=64, blank=True)
    vat_number = models.CharField(max_length=64, blank=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=64, blank=True)
    iban = models.CharField(max_length=64, blank=True)
    signatory_name = models.CharField(max_length=255, blank=True)
    website = models.URLField(max_length=500, blank=True)
    version = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "company_profiles"
        ordering = ("legal_name", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "registry_code"),
                condition=~Q(registry_code=""),
                name="unique_organization_company_registry_code",
            )
        ]


class ContractTemplate(OrganizationScopedModel):
    """Immutable organization-owned version of an HTML contract template."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_profile = models.ForeignKey(
        CompanyProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contract_templates",
    )
    template_key = models.SlugField(max_length=80)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    html = models.TextField()
    version = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    supersedes = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="successor_versions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_contract_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    organization_parent_fields = ("company_profile",)

    class Meta:
        db_table = "contract_templates"
        ordering = ("template_key", "-version")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "template_key", "version"),
                name="unique_organization_contract_template_version",
            ),
            models.UniqueConstraint(
                fields=("organization", "template_key"),
                condition=Q(is_active=True),
                name="unique_active_organization_contract_template",
            ),
        ]


class Contract(OrganizationScopedModel):
    id = models.CharField(primary_key=True, max_length=100)
    document = models.BinaryField(null=True, blank=True, db_column="contract")
    document_file = models.FileField(upload_to="contracts/%Y/%m", null=True, blank=True)
    base_id = models.CharField(max_length=50, blank=True)
    source_deal = models.ForeignKey("Deal", null=True, blank=True, on_delete=models.SET_NULL, related_name="contracts")
    source_offer = models.ForeignKey("DealOffer", null=True, blank=True, on_delete=models.SET_NULL, related_name="contracts")
    template_version = models.ForeignKey(
        ContractTemplate,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="generated_contracts",
    )
    template_snapshot = models.JSONField(default=dict, blank=True)
    version = models.PositiveBigIntegerField(default=1)
    organization_parent_fields = ("source_deal", "source_offer")

    class Meta:
        db_table = "contracts"


class ContractHistory(OrganizationScopedModel):
    id = models.CharField(primary_key=True, max_length=100)
    sellers = models.CharField(max_length=1000)
    buyer = models.CharField(max_length=100)
    contract_number = models.CharField(max_length=50, db_column="contract_no")
    created_at = models.DateTimeField(db_column="created")
    data = models.JSONField(default=dict)
    cadastres = models.CharField(max_length=100)

    class Meta:
        db_table = "contract_history"
        ordering = ("-created_at",)


class DealStage(models.TextChoices):
    QUALIFICATION = "QUALIFICATION", "Qualification"
    EVALUATION = "EVALUATION", "Evaluation"
    NEGOTIATION = "NEGOTIATION", "Negotiation"
    WON = "WON", "Won"
    LOST = "LOST", "Lost"
    CANCELLED = "CANCELLED", "Cancelled"


class Deal(OrganizationScopedModel):
    """Commercial case for one owner and one or more selected cadastral units."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="deals")
    parcels = models.ManyToManyField("forestry.Cadastre", related_name="deals")
    sale_subject = models.CharField(max_length=10, choices=(("FOREST", "Forest"), ("LAND", "Land"), ("BOTH", "Both")))
    stage = models.CharField(max_length=20, choices=DealStage.choices, default=DealStage.QUALIFICATION)
    decision_maker = models.CharField(max_length=200, blank=True)
    sale_timeframe = models.CharField(max_length=200, blank=True)
    price_expectation = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    qualification_notes = models.TextField(blank=True)
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="evaluated_deals")
    evaluation_status = models.CharField(max_length=20, blank=True)
    estimated_min_price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    estimated_max_price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    recommended_purchase_price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    internal_min_price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    proposed_offer_price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    offer_valid_until = models.DateField(null=True, blank=True)
    evaluation_assumptions = models.TextField(blank=True)
    evaluation_risks = models.TextField(blank=True)
    returned_reason = models.TextField(blank=True)
    loss_reason = models.CharField(max_length=100, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_deals")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveBigIntegerField(default=1)
    organization_parent_fields = ("owner",)

    class Meta:
        db_table = "commercial_deals"
        ordering = ("-updated_at",)
        indexes = [models.Index(fields=("organization", "owner", "stage"), name="deal_organization_owner_idx"), models.Index(fields=("organization", "stage", "updated_at"), name="deal_organization_stage_idx")]
class DealOffer(OrganizationScopedModel):
    class Kind(models.TextChoices):
        OFFER = "OFFER", "Offer"
        COUNTEROFFER = "COUNTEROFFER", "Counteroffer"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SENT = "SENT", "Sent"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name="offers")
    revision = models.PositiveIntegerField()
    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    valid_until = models.DateField(null=True, blank=True)
    terms = models.TextField(blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_deal_offers")
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    organization_parent_fields = ("deal",)

    class Meta:
        db_table = "commercial_deal_offers"
        ordering = ("revision", "created_at")
        constraints = [models.UniqueConstraint(fields=("organization", "deal", "revision"), name="unique_organization_deal_offer_revision")]


class InheritanceCase(OrganizationScopedModel):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        WAITING = "WAITING", "Waiting"
        COMPLETED = "COMPLETED", "Completed"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="inheritance_cases")
    source_notice_number = models.CharField(max_length=64, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    announcement_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)
    certification_deadline = models.DateField(null=True, blank=True)
    notary_name = models.CharField(max_length=255, blank=True)
    notary_phone = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_inheritance_cases")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveBigIntegerField(default=1)
    organization_parent_fields = ("owner",)

    class Meta:
        db_table = "inheritance_cases"
        ordering = ("-updated_at",)
        indexes = [models.Index(fields=("organization", "status", "assigned_to"), name="inherit_case_organization_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "owner", "source_notice_number"),
                condition=~Q(source_notice_number=""),
                name="unique_organization_inheritance_case",
            )
        ]


class InheritanceHeir(OrganizationScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inheritance_case = models.ForeignKey(InheritanceCase, on_delete=models.CASCADE, related_name="heirs")
    display_name = models.CharField(max_length=255)
    personal_code = models.CharField(max_length=50, blank=True)
    registry_code = models.CharField(max_length=50, blank=True)
    inheritance_share = models.CharField(max_length=100, blank=True)
    relation_to_deceased = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=254, blank=True)
    contact_status = models.CharField(max_length=100, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_inheritance_heirs")
    source = models.CharField(max_length=100, blank=True)
    organization_parent_fields = ("inheritance_case",)

    class Meta:
        db_table = "inheritance_heirs"
        ordering = ("display_name",)


class InheritanceCaseEvent(OrganizationScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inheritance_case = models.ForeignKey(InheritanceCase, on_delete=models.CASCADE, related_name="events")
    type = models.CharField(max_length=100)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="inheritance_events")
    created_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("inheritance_case",)

    class Meta:
        db_table = "inheritance_case_events"
        ordering = ("-created_at",)


class OwnerImportBatch(OrganizationScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="owner_import_batches")
    created_count = models.PositiveIntegerField(default=0)
    rejected_rows = models.JSONField(default=list, blank=True)
    committed_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("creator",)

    class Meta:
        db_table = "owner_import_batches"
        ordering = ("-committed_at",)


class OwnershipTransitionEvent(OrganizationScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Owner, null=True, blank=True, on_delete=models.SET_NULL, related_name="ownership_transitions")
    cadastre = models.ForeignKey("forestry.Cadastre", null=True, blank=True, on_delete=models.SET_NULL, related_name="ownership_transitions")
    event_type = models.CharField(max_length=100)
    occurred_at = models.DateTimeField(null=True, blank=True)
    source_reference = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    organization_parent_fields = ("owner", "cadastre")

    class Meta:
        db_table = "ownership_transition_events"
        ordering = ("-occurred_at", "-recorded_at")
        indexes = [models.Index(fields=("organization", "owner", "occurred_at"), name="ownership_org_owner_idx")]
