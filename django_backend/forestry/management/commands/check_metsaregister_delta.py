"""Run the same CQL-filtered delta check used by the Celery Beat task."""

from django.core.management.base import BaseCommand

from forestry.tasks import run_metsaregister_delta_check


class Command(BaseCommand):
    help = "Run the auditable Metsaregister CQL delta check once outside Celery Beat."

    def handle(self, *args, **options):
        result = run_metsaregister_delta_check.run()
        self.stdout.write(self.style.SUCCESS(f"Metsaregister CQL delta check completed: {result}"))
