"""Safe operator wrapper around the legacy MetsIS importer.

Dry-run is the default. A real write requires --confirm-write and records a
checkpoint artifact so an interrupted cutover can be resumed deterministically.
"""
from __future__ import annotations

import json
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Run the legacy cutover importer with dry-run, checkpoint and resume safeguards."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True)
        parser.add_argument("--confirm-write", action="store_true")
        parser.add_argument("--checkpoint", default="legacy-cutover-checkpoint.json")
        parser.add_argument("--resume", action="store_true")
        parser.add_argument("--quarantine", default="legacy-cutover-quarantine.jsonl")

    def handle(self, *args, **options):
        checkpoint_path = Path(options["checkpoint"])
        if options["resume"] and checkpoint_path.exists():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint.get("status") == "completed":
                self.stdout.write(self.style.SUCCESS("Checkpoint is already completed; nothing to resume."))
                return
        elif options["resume"]:
            raise CommandError("--resume requires an existing checkpoint file.")

        checkpoint = {
            "organization": options["organization"],
            "startedAt": timezone.now().isoformat(),
            "status": "running",
            "mode": "write" if options["confirm_write"] else "dry-run",
            "quarantine": options["quarantine"],
        }
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

        if options["confirm_write"]:
            call_command("import_legacy_metsis", "--confirm", "--organization", options["organization"])
        else:
            # Run the exact importer against the target transaction and force rollback.
            # Source is opened read-only by convention; target writes never escape dry-run.
            with transaction.atomic():
                call_command("import_legacy_metsis", "--confirm", "--organization", options["organization"])
                transaction.set_rollback(True)

        checkpoint.update({"status": "completed", "finishedAt": timezone.now().isoformat()})
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Legacy cutover {checkpoint['mode']} completed."))
