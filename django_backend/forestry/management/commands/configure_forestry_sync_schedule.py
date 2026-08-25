"""Explain the Celery Beat configuration used for ForestIQ data refreshes."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Display the Celery Beat schedule configuration for data refreshes."

    def add_arguments(self, parser):
        parser.add_argument("--check", action="store_true", help="Exit successfully after printing the configured scheduler.")

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Celery Beat schedules ForestIQ portfolio and Forestek refreshes from CELERY_BEAT_SCHEDULE."))
        self.stdout.write("Start the scheduler with: celery -A config beat --loglevel=INFO")
