"""Run the same CQL-filtered delta check used by the Celery Beat task."""

from django.core.management.base import BaseCommand, CommandError

from accounts.organization_selection import active_organization
from forestry.tasks import run_metsaregister_delta_check


class Command(BaseCommand):
    help = "Run the auditable Metsaregister CQL delta check once outside Celery Beat."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True, help="Organization UUID or slug that owns the delta audit run")

    def handle(self, *args, **options):
        organization = active_organization(options["organization"])
        if organization is None:
            raise CommandError("--organization must identify an active organization by UUID or slug.")
        result = run_metsaregister_delta_check.run(str(organization.id))
        self.stdout.write(self.style.SUCCESS(f"Metsaregister CQL delta check completed: {result}"))
