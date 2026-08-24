"""Register Django Q schedules for ForestIQ data refreshes."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_q.models import Schedule


class Command(BaseCommand):
    help = "Create or update daily Django Q jobs for cadastral and Forestek owner–cadastre sync."

    def add_arguments(self, parser):
        parser.add_argument("--hour", type=int, default=3, choices=range(0, 24), help="Local hour for the daily WFS refresh")
        parser.add_argument(
            "--forestek-hour",
            type=int,
            default=4,
            choices=range(0, 24),
            help="Local hour for the daily Forestek owner–cadastre refresh",
        )

    def handle(self, *args, **options):
        now = timezone.localtime()
        self._upsert_schedule(
            name="forestiq-daily-portfolio-sync",
            func="forestry.tasks.enqueue_portfolio_sync",
            hour=options["hour"],
            now=now,
        )
        self._upsert_schedule(
            name="forestiq-daily-forestek-owner-cadastre-sync",
            func="forestry.tasks.enqueue_forestek_portfolio_sync",
            hour=options["forestek_hour"],
            now=now,
        )

    def _upsert_schedule(self, *, name: str, func: str, hour: int, now) -> None:
        next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        schedule, _ = Schedule.objects.update_or_create(
            name=name,
            defaults={
                "func": func,
                "schedule_type": Schedule.DAILY,
                "repeats": -1,
                "next_run": next_run,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Schedule {schedule.name} ({schedule.func}) next runs at {schedule.next_run}"))
