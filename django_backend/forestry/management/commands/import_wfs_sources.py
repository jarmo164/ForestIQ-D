"""Import public WFS data for selected ForestIQ cadastral units."""

from django.core.management.base import BaseCommand, CommandError

from accounts.organization_selection import active_organization
from accounts.organization_context import organization_scope
from forestry.services.import_runner import WFS_SOURCES, configured_sources, run_cadastre_import, selected_cadastres


class Command(BaseCommand):
    help = "Import cadastre, forest-registry and optional SOOS WFS sources with an auditable run per cadastral unit."

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group(required=True)
        target.add_argument("--cadastre", help="Exact cadastral identifier to import")
        target.add_argument("--all", action="store_true", help="Import all ForestIQ cadastral units")
        parser.add_argument("--source", choices=("all", *WFS_SOURCES.keys()), default="all", help="WFS source to import; optional SOOS is skipped for --source all when unset")
        parser.add_argument("--limit", type=int, help="Maximum number of cadastral units when --all is used")
        parser.add_argument("--dry-run", action="store_true", help="Validate configuration and print the planned scope without requests or database writes")
        parser.add_argument("--continue-on-error", action="store_true", help="Continue with later sources and cadastral units after an external-source error")
        parser.add_argument("--organization", required=True, help="Organization UUID or slug that owns the import")

    def handle(self, *args, **options):
        organization = active_organization(options["organization"])
        if organization is None:
            raise CommandError("--organization must identify an active organization by UUID or slug.")
        try:
            sources, skipped = configured_sources(WFS_SOURCES, options["source"])
            with organization_scope(organization.id):
                cadastres = selected_cadastres(cadastre_id=options["cadastre"], all_cadastres=options["all"], limit=options["limit"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        source_names = ", ".join(source.key for source in sources)
        for entry in skipped:
            self.stdout.write(self.style.WARNING(f"Skipped {entry}."))
        if options["dry_run"]:
            self.stdout.write(f"Dry run: would import WFS sources [{source_names}] for {len(cadastres)} cadastral unit(s): {', '.join(item.id for item in cadastres)}")
            return
        failed = 0
        for cadastre in cadastres:
            run = run_cadastre_import(cadastre=cadastre, organization_id=str(organization.id), sources=sources, category="wfs", continue_on_error=options["continue_on_error"])
            self.stdout.write(f"{cadastre.id}: run {run.id} {run.status} {run.result}")
            if run.status == "FAILED":
                failed += 1
                if not options["continue_on_error"]:
                    raise CommandError(f"Import failed for {cadastre.id}: {run.error_message}")
        if failed:
            raise CommandError(f"WFS import completed with {failed} failed cadastral unit(s).")
