"""Initial full Metsaregister import followed by notifications for newly seen allocations."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.organization_selection import active_organization
from accounts.organization_context import organization_scope
from forestry.models import DataSyncRun
from forestry.services.external_sync import ExternalSourceError
from forestry.services.metsaregister_full_import import import_all_metsaregister


class Command(BaseCommand):
    help = "Import all Metsaregister allocations; use CQL notification queries only for newly discovered allocations."

    def add_arguments(self, parser):
        parser.add_argument("--page-size", type=int, default=settings.FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE)
        parser.add_argument("--dry-run", action="store_true", help="Validate layer configuration without WFS calls or writes")
        parser.add_argument("--without-notifications", action="store_true", help="Import allocations but do not retrieve notifications for new ones")
        parser.add_argument("--organization", required=True, help="Organization UUID or slug that will own imported records")

    def handle(self, *args, **options):
        if options["page_size"] < 1 or options["page_size"] > 10000:
            raise CommandError("--page-size must be between 1 and 10000.")
        if not settings.FORESTIQ_METSAREGISTER_WFS_URL or not settings.FORESTIQ_METSAREGISTER_FULL_WFS_LAYER:
            raise CommandError("FORESTIQ_METSAREGISTER_WFS_URL and FORESTIQ_METSAREGISTER_FULL_WFS_LAYER are required.")
        organization = active_organization(options["organization"])
        if organization is None:
            raise CommandError("--organization must identify an active organization by UUID or slug.")
        if options["dry_run"]:
            notice_state = "disabled" if options["without_notifications"] else ("enabled" if settings.FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER else "not configured; new notifications will be skipped")
            self.stdout.write(f"Dry run: would import all allocations from {settings.FORESTIQ_METSAREGISTER_FULL_WFS_LAYER} in pages of {options['page_size']}; notification import is {notice_state}.")
            return
        with organization_scope(organization.id):
            run = DataSyncRun.objects.create(source="cli:metsaregister-full", status=DataSyncRun.Status.RUNNING, started_at=timezone.now())
            try:
                report = import_all_metsaregister(organization_id=str(organization.id), page_size=options["page_size"], fetch_notifications=not options["without_notifications"])
            except Exception as exc:
                run.status, run.error_message, run.finished_at = DataSyncRun.Status.FAILED, str(exc)[:4000], timezone.now()
                run.save(update_fields=("status", "error_message", "finished_at"))
                if isinstance(exc, ExternalSourceError):
                    raise CommandError(str(exc)) from exc
                raise
            run.status, run.finished_at, run.result = DataSyncRun.Status.SUCCEEDED, timezone.now(), report.data()
            run.save(update_fields=("status", "finished_at", "result"))
        self.stdout.write(self.style.SUCCESS(f"Metsaregister full import completed: {report.data()}"))
