"""Verify that every AUTH-01 business record has a consistent organization owner."""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import F

from accounts.models import Organization, OrganizationMembership, User
from forestry.models import (
    CadastreLabel,
    CadastreNotification,
    CadastreSubPart,
    DataSyncRun,
    ForestRegistryFeature,
    InheritanceSignal,
    OwnerCadastre,
    OwnerFollowing,
    OwnerLog,
)
from operations.models import (
    Contract,
    Deal,
    DealOffer,
    DirectMessage,
    InheritanceCase,
    InheritanceCaseEvent,
    InheritanceHeir,
    OwnershipTransitionEvent,
    Reminder,
)


def parent_mismatch_count(model, parent_field: str, parent_organization_field: str | None = None) -> int:
    """Return rows whose stored organization differs from the parent aggregate."""

    parent_organization_field = parent_organization_field or f"{parent_field}__organization"
    return (
        model.objects.filter(**{f"{parent_field}__isnull": False})
        .exclude(organization_id=F(parent_organization_field))
        .count()
    )


class Command(BaseCommand):
    help = "Verify the AUTH-01 organization backfill without changing data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fail-on-issues",
            action="store_true",
            help="Exit with a non-zero status when an ownership mismatch is found.",
        )

    def handle(self, *args, **options):
        checks = {
            "organizations": Organization.objects.count(),
            "users_without_default_membership": User.objects.filter(default_organization__isnull=False)
            .exclude(organization_memberships__organization=F("default_organization"))
            .count(),
            "owner_cadastre.owner": parent_mismatch_count(OwnerCadastre, "owner"),
            "owner_cadastre.cadastre": parent_mismatch_count(OwnerCadastre, "cadastre"),
            "owner_log.owner": parent_mismatch_count(OwnerLog, "owner"),
            "cadastre_label.cadastre": parent_mismatch_count(CadastreLabel, "cadastre"),
            "cadastre_sub_part.cadastre": parent_mismatch_count(CadastreSubPart, "cadastre"),
            "cadastre_notification.cadastre": parent_mismatch_count(CadastreNotification, "cadastre"),
            "forest_registry_feature.cadastre": parent_mismatch_count(ForestRegistryFeature, "cadastre"),
            "owner_following.owner": parent_mismatch_count(OwnerFollowing, "owner"),
            "owner_following.user": parent_mismatch_count(OwnerFollowing, "user", "user__default_organization"),
            "data_sync_run.cadastre": parent_mismatch_count(DataSyncRun, "cadastre"),
            "data_sync_run.requested_by": parent_mismatch_count(DataSyncRun, "requested_by", "requested_by__default_organization"),
            "inheritance_signal.owner": parent_mismatch_count(InheritanceSignal, "owner"),
            "inheritance_signal.cadastre": parent_mismatch_count(InheritanceSignal, "cadastre"),
            "reminder.owner": parent_mismatch_count(Reminder, "owner"),
            "reminder.creator": parent_mismatch_count(Reminder, "creator", "creator__default_organization"),
            "direct_message.sender": parent_mismatch_count(DirectMessage, "sender", "sender__default_organization"),
            "direct_message.recipient": parent_mismatch_count(DirectMessage, "recipient", "recipient__default_organization"),
            "deal.owner": parent_mismatch_count(Deal, "owner"),
            "deal_offer.deal": parent_mismatch_count(DealOffer, "deal"),
            "contract.source_deal": parent_mismatch_count(Contract, "source_deal"),
            "contract.source_offer": parent_mismatch_count(Contract, "source_offer"),
            "inheritance_case.owner": parent_mismatch_count(InheritanceCase, "owner"),
            "inheritance_heir.case": parent_mismatch_count(InheritanceHeir, "inheritance_case"),
            "inheritance_event.case": parent_mismatch_count(InheritanceCaseEvent, "inheritance_case"),
            "ownership_transition.owner": parent_mismatch_count(OwnershipTransitionEvent, "owner"),
            "ownership_transition.cadastre": parent_mismatch_count(OwnershipTransitionEvent, "cadastre"),
            "memberships": OrganizationMembership.objects.count(),
        }
        issue_counts = {name: count for name, count in checks.items() if name != "organizations" and count}

        self.stdout.write(f"Organizations: {checks['organizations']}")
        self.stdout.write(f"Memberships: {checks['memberships']}")
        for name, count in checks.items():
            if name not in {"organizations", "memberships"}:
                self.stdout.write(f"{name}: {count}")

        if issue_counts:
            message = "Organization backfill verification found mismatches: " + ", ".join(
                f"{name}={count}" for name, count in issue_counts.items()
            )
            if options["fail_on_issues"]:
                raise CommandError(message)
            self.stderr.write(self.style.WARNING(message))
            return

        self.stdout.write(self.style.SUCCESS("Organization backfill verification passed."))
