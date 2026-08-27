"""Safe, idempotent imports for public WFS and authorised private data sources."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any
from uuid import UUID

import requests
from django.conf import settings
from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.geos import MultiPolygon
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from accounts.organization_context import current_organization_id
from forestry.models import (
    Cadastre,
    CadastreSubPart,
    ForestRegistryFeature,
    InheritanceSignal,
    Owner,
    OwnerCadastre,
)
from forestry.services.wfs_client import WfsClient, WfsClientError, wfs_client


class ExternalSourceError(RuntimeError):
    """A source returned an invalid or unavailable response."""


def _require_organization_context(organization_id: str) -> UUID:
    """Refuse direct background writes that are not bound to their supplied tenant."""

    expected = UUID(str(organization_id))
    if current_organization_id() != expected:
        raise ValueError("External synchronization requires the matching organization context.")
    return expected


def geometry_from_geojson(geometry: dict[str, Any], *, polygon_only: bool = False):
    """Parse, normalise and validate EPSG:3301 GeoJSON before persistence."""
    if not isinstance(geometry, dict) or not geometry.get("type") or "coordinates" not in geometry:
        raise ExternalSourceError("External source returned an incomplete geometry")
    try:
        parsed = OGRGeometry(json.dumps(geometry)).geos
        parsed.srid = 3301
    except (TypeError, ValueError) as exc:
        raise ExternalSourceError("External source returned malformed GeoJSON") from exc
    if polygon_only and parsed.geom_type == "Polygon":
        parsed = MultiPolygon(parsed, srid=3301)
    if polygon_only and parsed.geom_type != "MultiPolygon":
        raise ExternalSourceError("Cadastre geometry must be a Polygon or MultiPolygon")
    if parsed.empty:
        raise ExternalSourceError("External source returned an empty geometry")
    if not parsed.valid:
        parsed = parsed.buffer(0)
    if parsed.empty or not parsed.valid:
        raise ExternalSourceError("External source returned an invalid geometry")
    return parsed


def _headers(*, token: str = "") -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": settings.FORESTIQ_SYNC_USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _datetime(value: Any):
    if not value:
        return None
    if isinstance(value, str):
        return parse_datetime(value.replace("Z", "+00:00"))
    return None


def _date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return parse_date(str(value))


def _safe_cql_equals(field: str, value: str) -> str:
    if not field.replace("_", "").isalnum():
        raise ExternalSourceError("WFS filter field contains unsupported characters")
    return f"{field}='{value.replace("'", "''")}'"


def wfs_features(
    base_url: str,
    layer: str,
    *,
    field: str,
    value: str,
    client: WfsClient | None = None,
) -> list[dict[str, Any]]:
    """Return paginated, policy-bounded GeoJSON features for one exact identifier."""

    if not base_url or not layer:
        return []
    try:
        client = client or wfs_client()
        page_size = min(settings.FORESTIQ_WFS_PAGE_SIZE, settings.FORESTIQ_WFS_MAX_FEATURES)
        return [
            feature
            for page in client.iter_feature_pages(
                base_url=base_url,
                layer=layer,
                page_size=page_size,
                cql_filter=_safe_cql_equals(field, value),
                headers=_headers(),
            )
            for feature in page
        ]
    except WfsClientError as exc:
        raise ExternalSourceError(str(exc)) from exc


def _iter_xy(value: Any) -> Iterable[tuple[float, float]]:
    if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
        yield float(value[0]), float(value[1])
    elif isinstance(value, list):
        for item in value:
            yield from _iter_xy(item)


def _centroid(geometry: dict[str, Any]) -> dict[str, float]:
    points = list(_iter_xy(geometry.get("coordinates", [])))
    if not points:
        return {}
    return {
        "x": round(sum(point[0] for point in points) / len(points), 3),
        "y": round(sum(point[1] for point in points) / len(points), 3),
        "srid": 3301,
    }


def sync_cadastre_wfs(cadastre_id: str, *, organization_id: str) -> int:
    _require_organization_context(organization_id)
    cadastre = Cadastre.objects.get(id=cadastre_id)
    features = wfs_features(
        settings.FORESTIQ_CADASTRE_WFS_URL,
        settings.FORESTIQ_CADASTRE_WFS_LAYER,
        field="tunnus",
        value=cadastre.id,
    )
    if not features:
        return 0
    feature = features[0]
    properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
    with transaction.atomic():
        cadastre.municipality = str(properties.get("ov_nimi") or cadastre.municipality or "")
        cadastre.county = str(properties.get("mk_nimi") or cadastre.county or "")
        cadastre.address = str(properties.get("l_aadress") or cadastre.address or "")
        cadastre.registration_number = str(properties.get("kinnistu") or cadastre.registration_number or "")
        cadastre.type = str(properties.get("siht1") or cadastre.type or "")
        cadastre.polygon = geometry.get("coordinates", [])
        cadastre.centroid = _centroid(geometry)
        cadastre.boundary = geometry_from_geojson(geometry, polygon_only=True)
        cadastre.centroid_geometry = cadastre.boundary.centroid
        cadastre.area = _decimal(properties.get("pindala"))
        cadastre.arable_area = _decimal(properties.get("haritav"))
        cadastre.yard_area = _decimal(properties.get("ouemaa"))
        cadastre.meadow_area = _decimal(properties.get("rohumaa"))
        cadastre.forest_area = _decimal(properties.get("mets"))
        cadastre.other_area = _decimal(properties.get("muumaa"))
        cadastre.marked = str(properties.get("marked") or "").strip().lower() not in {"", "false", "0", "ei"}
        cadastre.save()
    return 1


def _feature_source_id(feature: dict[str, Any]) -> str:
    properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    candidate = properties.get("id") or properties.get("sys_id") or feature.get("id")
    if candidate not in (None, ""):
        return str(candidate)
    encoded = json.dumps(feature, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def sync_metsaregister_wfs(cadastre_id: str, *, organization_id: str) -> int:
    _require_organization_context(organization_id)
    cadastre = Cadastre.objects.get(id=cadastre_id)
    saved = 0
    source_layers = list(settings.FORESTIQ_METSAREGISTER_WFS_LAYERS)
    client = wfs_client()
    for layer in source_layers:
        features = wfs_features(
            settings.FORESTIQ_METSAREGISTER_WFS_URL,
            layer,
            field="katastri_nr",
            value=cadastre.id,
            client=client,
        )
        retained_ids: list[str] = []
        for feature in features:
            properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
            source_id = _feature_source_id(feature)
            retained_ids.append(source_id)
            geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
            ForestRegistryFeature.objects.update_or_create(
                source_layer=layer,
                source_id=source_id,
                defaults={
                    "cadastre": cadastre,
                    "subpart_code": properties.get("eraldise_nr"),
                    "title": f"Eraldis {properties.get('eraldise_nr')}" if properties.get("eraldise_nr") else layer,
                    "work_code": str(properties.get("raie_liik") or ""),
                    "decision": str(properties.get("otsus") or ""),
                    "area": _decimal(properties.get("pindala")),
                    "volume": _decimal(properties.get("tagavara_l_ha")),
                    "event_date": _datetime(properties.get("registreerimise_kp") or properties.get("invent_kp")),
                    "attributes": properties,
                    "geometry": geometry,
                    "spatial_geometry": geometry_from_geojson(geometry),
                },
            )
            if layer == "metsaregister:eraldis" and properties.get("eraldise_nr") is not None:
                CadastreSubPart.objects.update_or_create(
                    cadastre=cadastre,
                    sub_part_code=properties["eraldise_nr"],
                    defaults={
                        "tree_type_code": str(properties.get("peapuuliik_kood") or ""),
                        "area": _decimal(properties.get("pindala")),
                        "polygon": geometry.get("coordinates", []),
                        "boundary": geometry_from_geojson(geometry, polygon_only=True),
                    },
                )
            saved += 1
        ForestRegistryFeature.objects.filter(cadastre=cadastre, source_layer=layer).exclude(source_id__in=retained_ids).delete()
    return saved


def sync_optional_soos_wfs(cadastre_id: str, *, organization_id: str) -> int:
    _require_organization_context(organization_id)
    if not settings.FORESTIQ_SOOS_WFS_URL or not settings.FORESTIQ_SOOS_WFS_LAYER:
        return 0
    cadastre = Cadastre.objects.get(id=cadastre_id)
    layer = settings.FORESTIQ_SOOS_WFS_LAYER
    features = wfs_features(
        settings.FORESTIQ_SOOS_WFS_URL,
        layer,
        field=settings.FORESTIQ_SOOS_WFS_CADASTRE_FIELD,
        value=cadastre.id,
    )
    source_layer = f"soos:{layer}"
    retained_ids: list[str] = []
    for feature in features:
        properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        source_id = _feature_source_id(feature)
        retained_ids.append(source_id)
        ForestRegistryFeature.objects.update_or_create(
            source_layer=source_layer,
            source_id=source_id,
            defaults={
                "cadastre": cadastre,
                "title": str(properties.get("nimi") or properties.get("name") or layer),
                "attributes": properties,
                "geometry": feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {},
                "spatial_geometry": geometry_from_geojson(feature.get("geometry"), polygon_only=False),
            },
        )
    ForestRegistryFeature.objects.filter(cadastre=cadastre, source_layer=source_layer).exclude(source_id__in=retained_ids).delete()
    return len(features)


def _walk_owner_rows(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if any(key in value for key in ("nationalId", "personalCode", "ownerId")):
            yield value
        for nested in value.values():
            yield from _walk_owner_rows(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_owner_rows(nested)


def sync_forestek_owner_relations(cadastre_id: str, *, organization_id: str) -> int:
    _require_organization_context(organization_id)
    if not settings.FORESTEK_API_URL or not settings.FORESTEK_API_TOKEN:
        return 0
    cadastre = Cadastre.objects.get(id=cadastre_id)
    response = requests.get(
        f"{settings.FORESTEK_API_URL}/owners/{cadastre.id}",
        headers=_headers(token=settings.FORESTEK_API_TOKEN),
        timeout=settings.FORESTIQ_SYNC_HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    count = 0
    for row in _walk_owner_rows(payload):
        owner_id = str(row.get("nationalId") or row.get("personalCode") or row.get("ownerId") or "").strip()
        if not owner_id:
            continue
        owner, _ = Owner.objects.update_or_create(
            id=owner_id,
            defaults={
                "name": str(row.get("name") or owner_id),
                "type": "PERSON" if owner_id.isdigit() and len(owner_id) == 11 else "COMPANY",
            },
        )
        OwnerCadastre.objects.get_or_create(owner=owner, cadastre=cadastre)
        count += 1
    return count


def sync_parimus_inheritance(cadastre_id: str, *, organization_id: str) -> int:
    _require_organization_context(organization_id)
    if not settings.PARIMUS_API_URL or not settings.PARIMUS_API_TOKEN:
        return 0
    cadastre = Cadastre.objects.get(id=cadastre_id)
    owners = Owner.objects.filter(cadastres=cadastre).filter(id__regex=r"^\d{11}$")
    saved = 0
    for owner in owners:
        response = requests.get(
            f"{settings.PARIMUS_API_URL}/api/v1/notices/",
            params={"personal_code": owner.id},
            headers=_headers(token=settings.PARIMUS_API_TOKEN),
            timeout=settings.FORESTIQ_SYNC_HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        for notice in payload.get("results", []) if isinstance(payload, dict) else []:
            if not isinstance(notice, dict) or not notice.get("notice_number"):
                continue
            InheritanceSignal.objects.update_or_create(
                source_notice_number=str(notice["notice_number"]),
                cadastre=cadastre,
                defaults={
                    "owner": owner,
                    "announcement_date": _date(notice.get("announcement_date")),
                    "certification_deadline": _date(notice.get("certification_deadline")),
                    "deceased_name": str(notice.get("deceased_name") or ""),
                    "source_url": str(notice.get("source_url") or ""),
                    "payload": notice,
                },
            )
            saved += 1
    return saved
