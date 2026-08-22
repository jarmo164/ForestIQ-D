"""Register the once-daily portfolio WFS refresh with Django Q."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Create or update the daily Django Q job that queues ForestIQ cadastral refreshes."

    def add_arguments(self, parser):
        parser.add_argument("--hour", type=int, default=3, choices=range(0, 24), help="Local hour for the daily refresh")

    def handle(self, *args, **options):
        now = timezone.localtime()
        next_run = now.replace(hour=options["hour"], minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        schedule, _ = Schedule.objects.update_or_create(
            name="forestiq-daily-portfolio-sync",
            defaults={
                "func": "forestry.tasks.enqueue_portfolio_sync",
                "schedule_type": Schedule.DAILY,
                "repeats": -1,
                "next_run": next_run,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Schedule {schedule.name} next runs at {schedule.next_run}"))
