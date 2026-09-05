"""Regression tests for guarded legacy cutover tooling."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from forestry.management.commands.reconcile_legacy_cutover import _hash_rows


class LegacyCutoverCommandTests(TestCase):
    @patch.dict("os.environ", {"LEGACY_DATABASE_URL": "postgresql://readonly@example.test/metsis"})
    @patch("forestry.management.commands.migrate_legacy_cutover.call_command")
    @patch("forestry.management.commands.migrate_legacy_cutover._quarantine_source_rows", return_value=0)
    def test_dry_run_rolls_back_after_running_the_importer(self, quarantine, importer):
        with TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            quarantine_file = Path(directory) / "quarantine.jsonl"
            call_command(
                "migrate_legacy_cutover",
                "--organization",
                "demo",
                "--checkpoint",
                str(checkpoint),
                "--quarantine",
                str(quarantine_file),
            )

            state = json.loads(checkpoint.read_text(encoding="utf-8"))

        importer.assert_called_once_with("import_legacy_metsis", "--confirm", "--organization", "demo")
        quarantine.assert_called_once()
        self.assertEqual(state["mode"], "dry-run")
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["resumeStrategy"], "idempotent replay from source")

    @patch.dict("os.environ", {"LEGACY_DATABASE_URL": "postgresql://readonly@example.test/metsis"})
    @patch("forestry.management.commands.migrate_legacy_cutover.call_command")
    @patch("forestry.management.commands.migrate_legacy_cutover._quarantine_source_rows", return_value=0)
    def test_confirmed_run_delegates_to_idempotent_importer(self, quarantine, importer):
        with TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            call_command(
                "migrate_legacy_cutover",
                "--organization",
                "demo",
                "--confirm-write",
                "--checkpoint",
                str(checkpoint),
                "--quarantine",
                str(Path(directory) / "quarantine.jsonl"),
            )
            state = json.loads(checkpoint.read_text(encoding="utf-8"))

        importer.assert_called_once_with("import_legacy_metsis", "--confirm", "--organization", "demo")
        quarantine.assert_called_once()
        self.assertEqual(state["mode"], "write")
        self.assertEqual(state["status"], "completed")

    @patch.dict("os.environ", {"LEGACY_DATABASE_URL": "postgresql://readonly@example.test/metsis"})
    @patch("forestry.management.commands.migrate_legacy_cutover.call_command")
    @patch("forestry.management.commands.migrate_legacy_cutover._quarantine_source_rows", return_value=2)
    def test_quarantined_rows_block_any_write(self, quarantine, importer):
        with TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            with self.assertRaisesMessage(CommandError, "Cutover blocked: 2 malformed source row(s)"):
                call_command(
                    "migrate_legacy_cutover",
                    "--organization",
                    "demo",
                    "--confirm-write",
                    "--checkpoint",
                    str(checkpoint),
                    "--quarantine",
                    str(Path(directory) / "quarantine.jsonl"),
                )
            state = json.loads(checkpoint.read_text(encoding="utf-8"))

        quarantine.assert_called_once()
        importer.assert_not_called()
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["quarantinedRows"], 2)

    @patch.dict("os.environ", {"LEGACY_DATABASE_URL": "postgresql://readonly@example.test/metsis"})
    @patch("forestry.management.commands.migrate_legacy_cutover._quarantine_source_rows")
    def test_completed_checkpoint_makes_resume_idempotent(self, quarantine):
        with TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            checkpoint.write_text(json.dumps({"status": "completed"}), encoding="utf-8")
            call_command("migrate_legacy_cutover", "--organization", "demo", "--resume", "--checkpoint", str(checkpoint))

        quarantine.assert_not_called()


class LegacyReconciliationHashTests(TestCase):
    def test_row_checksum_is_order_independent_and_value_sensitive(self):
        expected = _hash_rows([{"id": "owner-2", "name": "B"}, {"id": "owner-1", "name": "A"}], ["id", "name"])
        reordered = _hash_rows([{"id": "owner-1", "name": "A"}, {"id": "owner-2", "name": "B"}], ["id", "name"])
        changed = _hash_rows([{"id": "owner-1", "name": "Changed"}, {"id": "owner-2", "name": "B"}], ["id", "name"])

        self.assertEqual(expected, reordered)
        self.assertNotEqual(expected, changed)
