"""Validate external-adapter runtime wiring without calling any provider."""
from __future__ import annotations

import redis
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


ADAPTERS = {
    "weasel": ("WEASEL_API_URL", "WEASEL_API_TOKEN"),
    "parimus": ("PARIMUS_API_URL", "PARIMUS_API_TOKEN"),
    "forestek": ("FORESTEK_API_URL", "FORESTEK_API_TOKEN"),
}


class Command(BaseCommand):
    help = "Check effective adapter and Redis/Celery configuration without provider requests."

    def add_arguments(self, parser):
        parser.add_argument("--check-redis", action="store_true")
        parser.add_argument("--require-adapter", action="append", choices=tuple(ADAPTERS))

    def handle(self, *args, **options):
        required = set(options["require_adapter"] or [])
        failed: list[str] = []
        for name, setting_names in ADAPTERS.items():
            missing = [setting_name for setting_name in setting_names if not getattr(settings, setting_name, "")]
            state = "NOT_CONFIGURED" if missing else "CONFIGURED"
            self.stdout.write(f"{name}: {state}")
            if name in required and missing:
                failed.append(f"{name}: missing {', '.join(missing)}")
        if options["check_redis"]:
            try:
                redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=3, socket_timeout=3).ping()
            except Exception as exc:
                failed.append(f"redis: {exc}")
            else:
                self.stdout.write("redis: OK")
        if failed:
            raise CommandError("; ".join(failed))
        self.stdout.write(self.style.SUCCESS("Integration runtime preflight passed."))
