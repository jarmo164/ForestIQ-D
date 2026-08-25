"""Import authorised Forestek and Pärimus data for selected cadastral units."""

from django.core.management.base import BaseCommand, CommandError

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

    def handle(self, *args, **options):
        try:
            sources, _skipped = configured_sources(API_SOURCES, options["source"])
            cadastres = selected_cadastres(cadastre_id=options["cadastre"], all_cadastres=options["all"], limit=options["limit"])
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        source_names = ", ".join(source.key for source in sources)
        if options["dry_run"]:
            self.stdout.write(f"Dry run: would import authorised API sources [{source_names}] for {len(cadastres)} cadastral unit(s): {', '.join(item.id for item in cadastres)}")
            return
        failed = 0
        for cadastre in cadastres:
            run = run_cadastre_import(cadastre=cadastre, sources=sources, category="api", continue_on_error=options["continue_on_error"])
            self.stdout.write(f"{cadastre.id}: run {run.id} {run.status} {run.result}")
            if run.status == "FAILED":
                failed += 1
                if not options["continue_on_error"]:
                    raise CommandError(f"Import failed for {cadastre.id}: {run.error_message}")
        if failed:
            raise CommandError(f"API import completed with {failed} failed cadastral unit(s).")
