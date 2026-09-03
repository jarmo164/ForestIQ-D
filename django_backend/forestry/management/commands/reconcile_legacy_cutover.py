"""Generate a deterministic legacy-vs-Django cutover readiness report."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from django.core.management.base import BaseCommand, CommandError

from accounts.models import OrganizationMembership, User
from accounts.organization_context import organization_scope
from accounts.organization_selection import active_organization
from forestry.models import Cadastre, CadastreNotification, CadastreSubPart, Owner, OwnerCadastre, OwnerLog
from operations.models import Contract, Deal


LEGACY_TABLES = {
    "users": "users",
    "owners": "owners",
    "cadastres": "cadastres",
    "ownerCadastres": "owner_cadastre",
    "subparts": "cadastre_sub_parts",
    "notices": "cadastre_notifications",
    "contracts": "contracts",
    "audits": "owner_log",
}


def _hash_rows(rows, keys):
    digest = hashlib.sha256()
    for row in sorted(rows, key=lambda item: tuple(str(item.get(key, "")) for key in keys)):
        digest.update("|".join(str(row.get(key, "")) for key in keys).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


class Command(BaseCommand):
    help = "Compare legacy MetsIS counts/checksums with Django and emit a go/no-go report."

    def add_arguments(self, parser):
        parser.add_argument("--organization", required=True)
        parser.add_argument("--output", default="cutover-reconciliation.json")
        parser.add_argument("--max-count-delta", type=int, default=0)
        parser.add_argument("--max-missing-ids", type=int, default=0)

    def handle(self, *args, **options):
        source_url = os.getenv("LEGACY_DATABASE_URL")
        if not source_url:
            raise CommandError("LEGACY_DATABASE_URL is required.")
        organization = active_organization(options["organization"])
        if organization is None:
            raise CommandError("Unknown or inactive organization.")

        legacy = {}
        with psycopg.connect(source_url, row_factory=dict_row) as source:
            for key, table in LEGACY_TABLES.items():
                with source.cursor() as cursor:
                    try:
                        cursor.execute(f'SELECT * FROM "{table}"')
                        rows = cursor.fetchall()
                    except Exception as exc:
                        source.rollback()
                        legacy[key] = {"available": False, "error": str(exc), "count": 0, "ids": []}
                        continue
                ids = [str(row.get("id")) for row in rows if row.get("id") is not None]
                legacy[key] = {
                    "available": True,
                    "count": len(rows),
                    "ids": ids,
                    "checksum": _hash_rows(rows, ["id"] if any("id" in row for row in rows) else list(rows[0].keys())[:2] if rows else ["id"]),
                }

        with organization_scope(organization.id):
            django_sets = {
                "users": set(OrganizationMembership.objects.filter(organization=organization).values_list("user_id", flat=True)),
                "owners": set(Owner.objects.values_list("id", flat=True)),
                "cadastres": set(Cadastre.objects.values_list("id", flat=True)),
                "ownerCadastres": {f"{owner}:{cad}" for owner, cad in OwnerCadastre.objects.values_list("owner_id", "cadastre_id")},
                "subparts": {f"{cad}:{code}" for cad, code in CadastreSubPart.objects.values_list("cadastre_id", "sub_part_code")},
                "notices": set(str(value) for value in CadastreNotification.objects.values_list("id", flat=True)),
                "contracts": set(str(value) for value in Contract.objects.values_list("id", flat=True)),
                "audits": set(str(value) for value in OwnerLog.objects.values_list("id", flat=True)),
                "deals": set(str(value) for value in Deal.objects.values_list("id", flat=True)),
            }

        comparisons = {}
        go = True
        for key, legacy_info in legacy.items():
            target = django_sets.get(key, set())
            source_ids = set(legacy_info.get("ids", []))
            # Relationship tables may not expose the same synthetic IDs, so count remains the stable gate there.
            comparable_ids = key not in {"ownerCadastres", "subparts"}
            missing = sorted(source_ids - set(map(str, target))) if comparable_ids else []
            extra = sorted(set(map(str, target)) - source_ids) if comparable_ids else []
            delta = len(target) - int(legacy_info.get("count", 0))
            passed = (
                legacy_info.get("available", False)
                and abs(delta) <= options["max_count_delta"]
                and len(missing) <= options["max_missing_ids"]
            )
            go = go and passed
            comparisons[key] = {
                "legacyCount": legacy_info.get("count", 0),
                "djangoCount": len(target),
                "countDelta": delta,
                "legacyChecksum": legacy_info.get("checksum"),
                "missingIds": missing[:100],
                "extraIds": extra[:100],
                "missingCount": len(missing),
                "extraCount": len(extra),
                "passed": passed,
            }
        report = {
            "organization": str(organization.id),
            "go": go,
            "thresholds": {"maxCountDelta": options["max_count_delta"], "maxMissingIds": options["max_missing_ids"]},
            "comparisons": comparisons,
            "note": "Deals are Django-native and are reported independently because legacy MetsIS did not have the same deal aggregate.",
            "djangoDealCount": len(django_sets["deals"]),
        }
        Path(options["output"]).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        self.stdout.write(json.dumps(report, indent=2, ensure_ascii=False))
        if not go:
            raise CommandError("Cutover reconciliation failed go/no-go thresholds.")
