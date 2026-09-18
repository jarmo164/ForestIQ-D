"""Import authorised Forestek and Pärimus data for selected cadastral units."""

from django.core.management.base import BaseCommand, CommandError

from accounts.organization_selection import active_organization
from accounts.organization_context import organization_scope
from forestry.models import DataSyncRun, ImportCheckpoint
from forestry.services.import_runner import API_SOURCES, configured_sources, run_cadastre_import, selected_cadastres


class Command(BaseCommand):
    help = "Import opt-in Forestek ownership relations and Pärimus notices with configuration preflight and audit runs."

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group(required=True)
        target.add_argument("--cadastre", help="Exact cadastral identifier to import")
        target.add_argument("--all", action="store_true", help="Import all ForestIQ cadastral units")
        parser.add_argument("--source", choices=("all", *API_SOURCES.keys()), default="all", help="Authorised API source to import")
        parser.add_argument("--limit", type=int, help="Maximum number of cadastral units when --all is used")
        parser.add_argument("--dry-run", action="store_true", help="Validate configuration and print the planned scope without API calls or database writes")
        parser.add_argument("--continue-on-error", action="store_true", help="Continue with later sources and cadastral units after an API error")
        parser.add_argument("--organization", required=True, help="Organization UUID or slug that owns the import")

    def handle(self, *args, **options):
        organization = active_organization(options["organization"])
        if organization is None:
            raise CommandError("--organization must identify an active organization by UUID or slug.")
        try:
            sources, _skipped = configured_sources(API_SOURCES, options["source"])
            with organization_scope(organization.id):
                cadastres = selected_cadastres(cadastre_id=options["cadastre"], all_cadastres=options["all"], limit=options["limit"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        source_names = ", ".join(source.key for source in sources)
        forestek_selected = any(source.key == "forestek" for source in sources)
        if forestek_selected:
            with organization_scope(organization.id):
                completed_ids = set(
                    ImportCheckpoint.objects.filter(source="forestek-initial", completed=True)
                    .values_list("source_layer", flat=True)
                )
            cadastres = [cadastre for cadastre in cadastres if cadastre.id not in completed_ids]
            if not cadastres:
                raise CommandError("Forestek initial import has already completed for the selected cadastral scope.")
        if options["dry_run"]:
            mode = "; Forestek is an unrepeatable initial import" if forestek_selected else ""
            self.stdout.write(f"Dry run: would import authorised API sources [{source_names}] for {len(cadastres)} cadastral unit(s): {', '.join(item.id for item in cadastres)}{mode}")
            return
        failed = 0
        for cadastre in cadastres:
            run = run_cadastre_import(cadastre=cadastre, organization_id=str(organization.id), sources=sources, category="api", continue_on_error=options["continue_on_error"])
            self.stdout.write(f"{cadastre.id}: run {run.id} {run.status} {run.result}")
            if forestek_selected:
                with organization_scope(organization.id):
                    checkpoint, _ = ImportCheckpoint.objects.get_or_create(
                        source="forestek-initial",
                        source_layer=cadastre.id,
                        defaults={"last_run": run},
                    )
                    checkpoint.last_run = run
                    checkpoint.completed = run.status == DataSyncRun.Status.SUCCESS
                    checkpoint.last_error = "" if checkpoint.completed else run.error_message
                    checkpoint.rows_completed = int(run.result.get("forestek", 0))
                    checkpoint.pages_completed = 1 if checkpoint.completed else 0
                    checkpoint.save(update_fields=("last_run", "completed", "last_error", "rows_completed", "pages_completed", "checkpointed_at"))
            if run.status != DataSyncRun.Status.SUCCESS:
                failed += 1
                if not options["continue_on_error"]:
                    raise CommandError(f"Import failed for {cadastre.id}: {run.error_message}")
        if failed:
            raise CommandError(f"API import completed with {failed} failed cadastral unit(s).")
