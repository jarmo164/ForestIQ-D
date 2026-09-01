"""Reconcile contract documents between the database and configured object storage."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from operations.models import Contract
from operations.services.contract_storage import reconcile_contract_storage


class Command(BaseCommand):
    help = "Report or repair contract document differences between the database and object storage."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Repair missing document objects, migrate legacy binaries, and delete orphan objects.")
        parser.add_argument("--organization", help="Restrict reconciliation to an organization UUID or slug.")

    def handle(self, *args, **options):
        contracts = Contract.objects.all()
        organization = options.get("organization")
        if organization:
            contracts = contracts.filter(organization__slug=organization)
            if not contracts.exists():
                try:
                    contracts = Contract.objects.filter(organization_id=organization)
                except (TypeError, ValueError) as exc:
                    raise CommandError("organization must be a known organization slug or UUID.") from exc
        report = reconcile_contract_storage(apply=options["apply"], contracts=contracts)
        self.stdout.write(json.dumps(report.data(), indent=2, sort_keys=True, default=str))
        if report.unrepaired_missing_objects:
            raise CommandError("Some named document objects are missing and have no retained database binary to restore them from.")
