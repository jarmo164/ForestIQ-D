"""Foreground import helpers shared by deterministic Django management commands."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Callable

from django.conf import settings
from django.utils import timezone

from config.observability import current_correlation_id

from accounts.organization_context import organization_scope
from forestry.models import Cadastre, DataSyncRun
from forestry.services.external_sync import (
    sync_cadastre_wfs,
    sync_forestek_owner_relations,
    sync_metsaregister_wfs,
    sync_optional_soos_wfs,
    sync_parimus_inheritance,
)


Importer = Callable[..., int]


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    importer: Importer
    required_settings: tuple[str, ...]
    optional: bool = False


WFS_SOURCES = {
    "cadastre": SourceDefinition("cadastre", sync_cadastre_wfs, ("FORESTIQ_CADASTRE_WFS_URL", "FORESTIQ_CADASTRE_WFS_LAYER")),
    "metsaregister": SourceDefinition("metsaregister", sync_metsaregister_wfs, ("FORESTIQ_METSAREGISTER_WFS_URL", "FORESTIQ_METSAREGISTER_WFS_LAYERS")),
    "soos": SourceDefinition("soos", sync_optional_soos_wfs, ("FORESTIQ_SOOS_WFS_URL", "FORESTIQ_SOOS_WFS_LAYER"), optional=True),
}

API_SOURCES = {
    "forestek": SourceDefinition("forestek", sync_forestek_owner_relations, ("FORESTEK_API_URL", "FORESTEK_API_TOKEN")),
    "parimus": SourceDefinition("parimus", sync_parimus_inheritance, ("PARIMUS_API_URL", "PARIMUS_API_TOKEN")),
}


def selected_cadastres(*, cadastre_id: str | None, all_cadastres: bool, limit: int | None) -> list[Cadastre]:
    if bool(cadastre_id) == bool(all_cadastres):
        raise ValueError("Choose exactly one of --cadastre or --all.")
    records = Cadastre.objects.order_by("id")
    if cadastre_id:
        records = records.filter(id=cadastre_id)
    if limit:
        records = records[:limit]
    result = list(records)
    if not result:
        raise ValueError("No matching cadastral units were found.")
    return result


def configured_sources(definitions: dict[str, SourceDefinition], requested: str) -> tuple[list[SourceDefinition], list[str]]:
    if requested != "all" and requested not in definitions:
        raise ValueError(f"Unknown source: {requested}.")
    candidates: Iterable[SourceDefinition] = definitions.values() if requested == "all" else (definitions[requested],)
    selected: list[SourceDefinition] = []
    skipped: list[str] = []
    for source in candidates:
        missing = [key for key in source.required_settings if not getattr(settings, key, None)]
        if missing:
            if source.optional and requested == "all":
                skipped.append(f"{source.key} (optional configuration is missing: {', '.join(missing)})")
                continue
            raise ValueError(f"{source.key} is not configured: {', '.join(missing)}.")
        selected.append(source)
    if not selected:
        raise ValueError("No requested data source is configured.")
    return selected, skipped


def run_cadastre_import(
    *,
    cadastre: Cadastre,
    organization_id: str,
    sources: list[SourceDefinition],
    category: str,
    continue_on_error: bool,
) -> DataSyncRun:
    """Run selected source importers synchronously and persist one audit record per cadastre."""

    with organization_scope(organization_id):
        scoped_cadastre = Cadastre.objects.get(id=cadastre.id)
        run = DataSyncRun.objects.create(
            cadastre=scoped_cadastre,
            source=f"cli:{category}:{','.join(source.key for source in sources)}",
            status=DataSyncRun.Status.RUNNING,
            started_at=timezone.now(),
            correlation_id=current_correlation_id(),
        )
        result: dict[str, Any] = {}
        errors: dict[str, str] = {}
        for source in sources:
            try:
                result[source.key] = source.importer(scoped_cadastre.id, organization_id=str(organization_id))
            except Exception as exc:  # External sources are intentionally surfaced in the durable audit record.
                errors[source.key] = str(exc)[:4000]
                if not continue_on_error:
                    break
        run.finished_at = timezone.now()
        run.result = result
        run.pages_processed = len(result)
        run.rows_processed = sum(value for value in result.values() if isinstance(value, int) and not isinstance(value, bool))
        run.cursor = {"cadastreId": scoped_cadastre.id}
        if errors:
            run.status = DataSyncRun.Status.PARTIAL if result else DataSyncRun.Status.FAILED
            run.result = {**result, "failed_sources": errors}
            run.error_message = "; ".join(f"{key}: {message}" for key, message in errors.items())[:4000]
        else:
            run.status = DataSyncRun.Status.SUCCESS
            run.error_message = ""
        run.save(
            update_fields=(
                "status",
                "started_at",
                "finished_at",
                "result",
                "error_message",
                "pages_processed",
                "rows_processed",
                "cursor",
                "correlation_id",
            )
        )
        return run
