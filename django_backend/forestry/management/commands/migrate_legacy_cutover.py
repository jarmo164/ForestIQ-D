"""Safe operator wrapper around the legacy MetsIS importer.

Dry-run is the default. A real write requires --confirm-write and records a
checkpoint artifact so an interrupted cutover can be resumed deterministically.
Malformed source rows are quarantined during preflight and block writes instead
of being silently discarded.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
from psycopg.errors import UndefinedTable
from psycopg.rows import dict_row
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone


PREFLIGHT_KEYS = {
    "users": ("id",),
    "privileges": ("id", "user_id"),
    "owners": ("id",),
    "cadastres": ("id",),
    "owner_cadastre": ("owner_id", "cadastre_id"),
    "cadastre_labels": ("id", "cadastre_id"),
    "cadastre_sub_parts": ("cadastre_id", "sub_part_code"),
    "cadastre_notifications": ("id", "notification_number", "cadastre_id"),
    "forest_registry_features": ("source_layer", "source_id", "cadastre_id"),
    "owner_log": ("id", "owner_id", "creator"),
    "persons_dump": ("id",),
    "reminders": ("id", "duetime"),
    "contracts": ("id",),
    "contract_history": ("id",),
}


def _quarantine_source_rows(source_url: str, output: Path) -> int:
    """Preflight required identity/relationship fields and write bad rows as JSONL."""
    quarantined = []
    with psycopg.connect(source_url, row_factory=dict_row) as source:
        for table, required in PREFLIGHT_KEYS.items():
            try:
                with source.cursor() as cursor:
                    cursor.execute(f'SELECT * FROM "{table}"')
                    for row_number, row in enumerate(cursor, start=1):
                        missing = [key for key in required if row.get(key) in (None, "")]
                        if missing:
                            quarantined.append(
                                {
                                    "table": table,
                                    "rowNumber": row_number,
                                    "reason": "missing_required_fields",
                                    "fields": missing,
                                    "row": dict(row),
                                }
                            )
            except UndefinedTable:
                source.rollback()
                continue
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for item in quarantined:
            handle.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
    return len(quarantined)


class Command(BaseCommand):
    help = "Run the legacy cutover importer with dry-run, quarantine, checkpoint and resume safeguards."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True)
        parser.add_argument("--confirm-write", action="store_true")
        parser.add_argument("--checkpoint", default="legacy-cutover-checkpoint.json")
        parser.add_argument("--resume", action="store_true")
        parser.add_argument("--quarantine", default="legacy-cutover-quarantine.jsonl")

    def handle(self, *args, **options):
        source_url = os.getenv("LEGACY_DATABASE_URL")
        if not source_url:
            raise CommandError("LEGACY_DATABASE_URL is required.")
        checkpoint_path = Path(options["checkpoint"])
        quarantine_path = Path(options["quarantine"])
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
            "status": "preflight",
            "mode": "write" if options["confirm_write"] else "dry-run",
            "quarantine": str(quarantine_path),
            "resumeStrategy": "idempotent replay from source",
        }
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

        quarantined = _quarantine_source_rows(source_url, quarantine_path)
        checkpoint["quarantinedRows"] = quarantined
        if quarantined:
            checkpoint.update({"status": "blocked", "finishedAt": timezone.now().isoformat()})
            checkpoint_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
            raise CommandError(
                f"Cutover blocked: {quarantined} malformed source row(s) were written to {quarantine_path}."
            )

        checkpoint["status"] = "running"
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        try:
            if options["confirm_write"]:
                call_command("import_legacy_metsis", "--confirm", "--organization", options["organization"])
            else:
                # Run the exact importer against the target transaction and force rollback.
                # Source is opened separately; target writes never escape dry-run.
                with transaction.atomic():
                    call_command("import_legacy_metsis", "--confirm", "--organization", options["organization"])
                    transaction.set_rollback(True)
        except Exception as exc:
            checkpoint.update({
                "status": "failed",
                "finishedAt": timezone.now().isoformat(),
                "error": str(exc)[:4000],
            })
            checkpoint_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
            raise

        checkpoint.update({"status": "completed", "finishedAt": timezone.now().isoformat()})
        checkpoint_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Legacy cutover {checkpoint['mode']} completed."))
