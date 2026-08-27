"""Full Metsaregister import with targeted notification retrieval for newly discovered subparts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal, InvalidOperation
import json
from typing import Any, Iterator
from uuid import UUID

import requests
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_datetime

from accounts.organization_context import current_organization_id
from forestry.models import Cadastre, CadastreNotification, CadastreSubPart, DataSyncRun, ForestRegistryFeature, ImportCheckpoint
from forestry.services.external_sync import ExternalSourceError, geometry_from_geojson
from forestry.services.wfs_client import WfsClient, WfsClientError


def _safe_field(name: str) -> str:
    if not name.replace("_", "").isalnum():
        raise ExternalSourceError("WFS CQL field contains unsupported characters")
    return name


def _require_organization_context(organization_id: str) -> UUID:
    """Ensure an import is executing under the tenant supplied to its caller."""

    expected = UUID(str(organization_id))
    if current_organization_id() != expected:
        raise ValueError("Metsaregister import requires the matching organization context.")
    return expected


def _cql_equals(values: dict[str, str | int]) -> str:
    parts = []
    for field, value in values.items():
        safe_field = _safe_field(field)
        if isinstance(value, int):
            parts.append(f"{safe_field}={value}")
        else:
            parts.append(f"{safe_field}='{str(value).replace("'", "''")}'")
    return " AND ".join(parts)


def _number(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _headers() -> dict[str, str]:
    return {"Accept": "application/json", "User-Agent": settings.FORESTIQ_SYNC_USER_AGENT}


def _feature_page(
    *,
    layer: str,
    start_index: int,
    page_size: int,
    cql_filter: str | None = None,
    client: WfsClient | None = None,
) -> list[dict[str, Any]]:
    """Fetch one policy-validated Metsaregister WFS page."""

    try:
        return (client or WfsClient(request_get=requests.get)).feature_page(
            base_url=settings.FORESTIQ_METSAREGISTER_WFS_URL,
            layer=layer,
            start_index=start_index,
            page_size=page_size,
            cql_filter=cql_filter,
            headers=_headers(),
        )
    except WfsClientError as exc:
        raise ExternalSourceError(str(exc)) from exc


def _pages(
    *,
    layer: str,
    page_size: int,
    cql_filter: str | None = None,
    start_index: int = 0,
) -> Iterator[list[dict[str, Any]]]:
    """Yield client-bounded pages from a cursor with one shared rate limiter."""

    try:
        yield from WfsClient(request_get=requests.get).iter_feature_pages(
            base_url=settings.FORESTIQ_METSAREGISTER_WFS_URL,
            layer=layer,
            page_size=page_size,
            cql_filter=cql_filter,
            headers=_headers(),
            start_index=start_index,
        )
    except WfsClientError as exc:
        raise ExternalSourceError(str(exc)) from exc


def _source_id(feature: dict[str, Any]) -> str:
    properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    candidate = properties.get("id") or properties.get("sys_id") or feature.get("id")
    if candidate not in (None, ""):
        return str(candidate)
    return str(abs(hash(json.dumps(feature, sort_keys=True, ensure_ascii=False))))


@dataclass
class FullImportReport:
    features: int = 0
    cadastres: int = 0
    new_subparts: int = 0
    updated_subparts: int = 0
    notifications: int = 0
    skipped_features: int = 0
    resumed_from: int = 0
    checkpoint_cursor: int = 0
    checkpoint_pages: int = 0

    def data(self) -> dict[str, int]:
        return asdict(self)


def _open_full_import_checkpoint(*, layer: str, run: DataSyncRun | None) -> ImportCheckpoint:
    """Reuse the last incomplete import cursor, or begin a separately auditable run."""

    checkpoint = (
        ImportCheckpoint.objects.filter(
            source="metsaregister-full",
            source_layer=layer,
            completed=False,
        )
        .order_by("-checkpointed_at", "-id")
        .first()
    )
    if checkpoint is None:
        return ImportCheckpoint.objects.create(
            source="metsaregister-full",
            source_layer=layer,
            last_run=run,
        )
    checkpoint.last_run = run
    checkpoint.last_error = ""
    checkpoint.save(update_fields=("last_run", "last_error", "checkpointed_at"))
    return checkpoint


def _confirm_checkpoint_page(
    checkpoint: ImportCheckpoint,
    *,
    page_size: int,
    run: DataSyncRun | None,
) -> None:
    """Persist only a completely stored page as the next safe restart cursor."""

    checkpoint.cursor += page_size
    checkpoint.pages_completed += 1
    checkpoint.rows_completed += page_size
    checkpoint.last_run = run
    checkpoint.last_error = ""
    checkpoint.save(
        update_fields=(
            "cursor",
            "pages_completed",
            "rows_completed",
            "last_run",
            "last_error",
            "checkpointed_at",
        )
    )


def _upsert_notification(*, cadastre: Cadastre, subpart_code: int, feature: dict[str, Any]) -> bool:
    properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    identifier = _int(properties.get("id") or properties.get("teatise_id") or properties.get("objectid") or feature.get("id"))
    number = _int(properties.get("teatise_nr") or properties.get("notification_number") or identifier)
    if identifier is None or number is None:
        return False
    CadastreNotification.objects.update_or_create(
        id=identifier,
        defaults={
            "notification_number": number,
            "cadastre": cadastre,
            "cadastre_subpart_code": _int(properties.get("eraldis_nr")) or subpart_code,
            "work_code": str(properties.get("raie_liik") or properties.get("work_code") or ""),
            "state": _int(properties.get("staatus") or properties.get("state")),
            "damage_code": str(properties.get("kahjustus") or properties.get("damage_code") or ""),
            "decision": str(properties.get("otsus") or properties.get("decision") or ""),
            "registration_date": parse_datetime(str(properties.get("registreerimise_kp") or "").replace("Z", "+00:00")),
            "confirmation_date": parse_datetime(str(properties.get("kinnitamise_kp") or "").replace("Z", "+00:00")),
            "area": _number(properties.get("pindala")),
            "amount_to_be_cut": _number(properties.get("raiemaht") or properties.get("amount_to_be_cut")),
            "archived": str(properties.get("archived") or "").lower() in {"true", "1", "yes"},
        },
    )
    return True


def _import_notifications_for_new_subpart(*, cadastre: Cadastre, subpart_code: int) -> int:
    layer = settings.FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER
    if not layer:
        return 0
    cql = _cql_equals({settings.FORESTIQ_METSAREGISTER_NOTIFICATION_CADASTRE_FIELD: cadastre.id, settings.FORESTIQ_METSAREGISTER_NOTIFICATION_SUBPART_FIELD: subpart_code})
    return sum(_upsert_notification(cadastre=cadastre, subpart_code=subpart_code, feature=feature) for feature in _feature_page(layer=layer, start_index=0, page_size=settings.FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE, cql_filter=cql))


def _store_allocation(*, report: FullImportReport, layer: str, feature: dict[str, Any], fetch_notifications: bool) -> None:
    report.features += 1
    properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    cadastre_id = str(properties.get("katastri_nr") or "").strip()
    subpart_code = _int(properties.get("eraldis_nr"))
    geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
    if not cadastre_id or subpart_code is None or not geometry:
        report.skipped_features += 1
        return
    with transaction.atomic():
        cadastre, created_cadastre = Cadastre.objects.get_or_create(id=cadastre_id)
        report.cadastres += int(created_cadastre)
        was_new = not CadastreSubPart.objects.filter(cadastre=cadastre, sub_part_code=subpart_code).exists()
        CadastreSubPart.objects.update_or_create(cadastre=cadastre, sub_part_code=subpart_code, defaults={"tree_type_code": str(properties.get("peapuuliik_kood") or ""), "area": _number(properties.get("pindala")), "polygon": geometry.get("coordinates", []), "boundary": geometry_from_geojson(geometry, polygon_only=True)})
        ForestRegistryFeature.objects.update_or_create(source_layer=layer, source_id=_source_id(feature), defaults={"cadastre": cadastre, "subpart_code": subpart_code, "title": f"Eraldis {subpart_code}", "work_code": str(properties.get("raie_liik") or ""), "decision": str(properties.get("otsus") or ""), "area": _number(properties.get("pindala")), "volume": _number(properties.get("tagavara_l_ha")), "attributes": properties, "geometry": geometry, "spatial_geometry": geometry_from_geojson(geometry)})
        if was_new:
            report.new_subparts += 1
            if fetch_notifications:
                report.notifications += _import_notifications_for_new_subpart(cadastre=cadastre, subpart_code=subpart_code)
        else:
            report.updated_subparts += 1


def import_all_metsaregister(
    *,
    organization_id: str,
    page_size: int | None = None,
    fetch_notifications: bool = True,
    run: DataSyncRun | None = None,
) -> FullImportReport:
    """Import every allocation from the last confirmed page, then close its checkpoint.

    Entity writes are idempotent `update_or_create` operations. If a worker stops
    before a page is confirmed, the prior cursor remains durable and the entire
    page can safely be requested and stored again on the next controlled run.
    """

    _require_organization_context(organization_id)
    layer = settings.FORESTIQ_METSAREGISTER_FULL_WFS_LAYER
    if not settings.FORESTIQ_METSAREGISTER_WFS_URL or not layer:
        raise ExternalSourceError("Metsaregister WFS URL and full-import layer must be configured")
    effective_page_size = page_size or settings.FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE
    checkpoint = _open_full_import_checkpoint(layer=layer, run=run)
    report = FullImportReport(
        resumed_from=checkpoint.cursor,
        checkpoint_cursor=checkpoint.cursor,
        checkpoint_pages=checkpoint.pages_completed,
    )
    try:
        for page in _pages(
            layer=layer,
            page_size=effective_page_size,
            start_index=checkpoint.cursor,
        ):
            for feature in page:
                _store_allocation(report=report, layer=layer, feature=feature, fetch_notifications=fetch_notifications)
            _confirm_checkpoint_page(checkpoint, page_size=len(page), run=run)
            report.checkpoint_cursor = checkpoint.cursor
            report.checkpoint_pages = checkpoint.pages_completed
    except Exception as exc:
        checkpoint.completed = False
        checkpoint.last_run = run
        checkpoint.last_error = str(exc)[:4000]
        checkpoint.save(update_fields=("completed", "last_run", "last_error", "checkpointed_at"))
        raise
    checkpoint.completed = True
    checkpoint.last_run = run
    checkpoint.last_error = ""
    checkpoint.save(update_fields=("completed", "last_run", "last_error", "checkpointed_at"))
    return report


def import_metsaregister_delta(
    *,
    organization_id: str,
    since: datetime,
    page_size: int | None = None,
    fetch_notifications: bool = True,
) -> FullImportReport:
    """Use a server-side CQL timestamp filter and persist only newly discovered allocations."""

    _require_organization_context(organization_id)
    layer = settings.FORESTIQ_METSAREGISTER_FULL_WFS_LAYER
    if not settings.FORESTIQ_METSAREGISTER_WFS_URL or not layer:
        raise ExternalSourceError("Metsaregister WFS URL and delta layer must be configured")
    if since.tzinfo is None:
        raise ValueError("Delta timestamp must be timezone-aware")
    timestamp = since.astimezone(datetime_timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    cql_filter = f"{_safe_field(settings.FORESTIQ_METSAREGISTER_DELTA_FIELD)} >= '{timestamp}'"
    report = FullImportReport()
    for page in _pages(layer=layer, page_size=page_size or settings.FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE, cql_filter=cql_filter):
        for feature in page:
            _store_allocation(report=report, layer=layer, feature=feature, fetch_notifications=fetch_notifications)
    return report
