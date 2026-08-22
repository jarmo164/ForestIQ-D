"""Queue or execute the WFS synchronisation for one or all ForestIQ cadastres."""

from django.core.management.base import BaseCommand, CommandError

from forestry.models import Cadastre, DataSyncRun
from forestry.tasks import enqueue_cadastre_sync, run_cadastre_sync


class Command(BaseCommand):
    help = "Queue an auditable WFS/registry refresh for one cadastral unit or the entire portfolio."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--cadastre", help="Cadastral identifier to refresh")
        group.add_argument("--all", action="store_true", help="Refresh every ForestIQ cadastral unit")
        parser.add_argument("--inline", action="store_true", help="Run in this process instead of submitting to Django Q")

    def handle(self, *args, **options):
        ids = [options["cadastre"]] if options["cadastre"] else list(Cadastre.objects.values_list("id", flat=True))
        if not ids:
            raise CommandError("No cadastral units were found.")
        for cadastre_id in ids:
            if not Cadastre.objects.filter(id=cadastre_id).exists():
                raise CommandError(f"Unknown cadastral unit: {cadastre_id}")
            if options["inline"]:
                run = DataSyncRun.objects.create(cadastre_id=cadastre_id, source="manual-inline")
                run_cadastre_sync(run.id)
                run.refresh_from_db()
            else:
                run = enqueue_cadastre_sync(cadastre_id, source="manual")
            self.stdout.write(f"{cadastre_id}: run {run.id} ({run.status})")
