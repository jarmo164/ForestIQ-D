"""Generation-based Metsaregister WFS staging, validation, publish and rollback."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import hashlib
import json

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from forestry.models import Cadastre, CadastreSubPart, ForestRegistryFeature
from forestry.p3_models import WfsGeneration, WfsGenerationFeature, WfsLayerManifest
from forestry.services.external_sync import (
    ExternalSourceError,
    _datetime,
    _decimal,
    _feature_source_id,
    geometry_from_geojson,
    wfs_features,
)


def _value_type(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float, Decimal)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _schema_fields_add(schema: dict[str, set[str]], properties: dict) -> None:
    for key, value in properties.items():
        schema[str(key)].add(_value_type(value))


def _normalise_schema(schema: dict[str, set[str]]) -> dict[str, list[str]]:
    return {key: sorted(values) for key, values in sorted(schema.items())}


def _schema_hash(schema_fields: dict) -> str:
    encoded = json.dumps(schema_fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def generation_schema_from_storage(generation: WfsGeneration) -> tuple[dict, str]:
    schema: dict[str, set[str]] = defaultdict(set)
    for properties in generation.features.values_list("properties", flat=True).iterator(chunk_size=1000):
        _schema_fields_add(schema, properties if isinstance(properties, dict) else {})
    fields = _normalise_schema(schema)
    return fields, _schema_hash(fields)


def ensure_default_manifests(*, organization_id) -> list[WfsLayerManifest]:
    """Create explicit manifests for configured Metsaregister layers without changing existing policy."""
    from django.conf import settings

    result = []
    for layer in settings.FORESTIQ_METSAREGISTER_WFS_LAYERS:
        key = layer.replace(":", "-").replace("_", "-").lower()[:100]
        item, _ = WfsLayerManifest.objects.get_or_create(
            organization_id=organization_id,
            source_layer=layer,
            defaults={"key": key, "cadastre_field": "katastri_nr"},
        )
        result.append(item)
    return result


def stage_generation(manifest: WfsLayerManifest, *, created_by=None) -> WfsGeneration:
    """Capture all organization-relevant cadastral features into immutable staging."""
    from django.conf import settings

    sequence = (manifest.generations.aggregate(value=Max("sequence"))["value"] or 0) + 1
    generation = WfsGeneration.objects.create(
        manifest=manifest,
        sequence=sequence,
        status=WfsGeneration.Status.STAGING,
        created_by=created_by,
    )
    schema: dict[str, set[str]] = defaultdict(set)
    feature_count = 0
    cadastre_count = 0
    try:
        for cadastre_id in Cadastre.objects.order_by("id").values_list("id", flat=True).iterator(chunk_size=250):
            features = wfs_features(
                settings.FORESTIQ_METSAREGISTER_WFS_URL,
                manifest.source_layer,
                field=manifest.cadastre_field,
                value=cadastre_id,
            )
            if not features:
                continue
            cadastre_count += 1
            staged = []
            for feature in features:
                properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
                geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
                _schema_fields_add(schema, properties)
                staged.append(
                    WfsGenerationFeature(
                        generation=generation,
                        cadastre_id=cadastre_id,
                        source_id=_feature_source_id(feature),
                        properties=properties,
                        geometry=geometry,
                    )
                )
            WfsGenerationFeature.objects.bulk_create(staged, batch_size=500)
            feature_count += len(staged)

        fields = _normalise_schema(schema)
        schema_hash = _schema_hash(fields)
        drift = bool(manifest.expected_schema_hash and manifest.expected_schema_hash != schema_hash)
        empty = feature_count == 0
        validation = {
            "featureCount": feature_count,
            "cadastreCount": cadastre_count,
            "schemaDrift": drift,
            "emptyGeneration": empty,
            "expectedSchemaHash": manifest.expected_schema_hash or None,
            "observedSchemaHash": schema_hash,
        }
        generation.feature_count = feature_count
        generation.cadastre_count = cadastre_count
        generation.schema_fields = fields
        generation.schema_hash = schema_hash
        generation.observed_at = timezone.now()
        generation.validation = validation
        generation.status = WfsGeneration.Status.FAILED if (drift or empty) else WfsGeneration.Status.READY
        generation.save(
            update_fields=(
                "feature_count", "cadastre_count", "schema_fields", "schema_hash",
                "observed_at", "validation", "status",
            )
        )
        if not manifest.expected_schema_hash and not empty:
            manifest.expected_schema_hash = schema_hash
            manifest.expected_schema_fields = fields
            manifest.save(update_fields=("expected_schema_hash", "expected_schema_fields", "updated_at"))
            validation["baselineEstablished"] = True
            generation.validation = validation
            generation.save(update_fields=("validation",))
        return generation
    except Exception as exc:
        generation.status = WfsGeneration.Status.FAILED
        generation.observed_at = timezone.now()
        generation.validation = {
            "featureCount": feature_count,
            "cadastreCount": cadastre_count,
            "error": str(exc)[:4000],
        }
        generation.feature_count = feature_count
        generation.cadastre_count = cadastre_count
        generation.save(
            update_fields=("status", "observed_at", "validation", "feature_count", "cadastre_count")
        )
        return generation


def approve_schema_drift(generation: WfsGeneration, *, actor, reason: str) -> WfsGeneration:
    reason = str(reason or "").strip()
    if generation.status != WfsGeneration.Status.FAILED or not generation.validation.get("schemaDrift"):
        raise ValueError("Only a generation blocked by schema drift can be approved.")
    if not generation.manifest.allow_schema_drift:
        raise ValueError("This manifest does not permit audited schema-drift approval.")
    if not reason:
        raise ValueError("A schema-drift approval reason is required.")
    generation.schema_drift_approved_by = actor
    generation.schema_drift_reason = reason
    generation.status = WfsGeneration.Status.READY
    generation.validation = {**generation.validation, "schemaDriftApproved": True, "schemaDriftReason": reason}
    generation.save(
        update_fields=("schema_drift_approved_by", "schema_drift_reason", "status", "validation")
    )
    manifest = generation.manifest
    manifest.expected_schema_hash = generation.schema_hash
    manifest.expected_schema_fields = generation.schema_fields
    manifest.save(update_fields=("expected_schema_hash", "expected_schema_fields", "updated_at"))
    return generation


def _projection_row(manifest: WfsLayerManifest, feature: WfsGenerationFeature, cadastre: Cadastre):
    properties = feature.properties if isinstance(feature.properties, dict) else {}
    geometry = feature.geometry if isinstance(feature.geometry, dict) else {}
    return ForestRegistryFeature(
        organization_id=manifest.organization_id,
        source_layer=manifest.source_layer,
        source_id=feature.source_id,
        cadastre=cadastre,
        subpart_code=properties.get("eraldise_nr"),
        title=f"Eraldis {properties.get('eraldise_nr')}" if properties.get("eraldise_nr") else manifest.source_layer,
        work_code=str(properties.get("raie_liik") or ""),
        decision=str(properties.get("otsus") or ""),
        area=_decimal(properties.get("pindala")),
        volume=_decimal(properties.get("tagavara_l_ha")),
        event_date=_datetime(properties.get("registreerimise_kp") or properties.get("invent_kp")),
        attributes=properties,
        geometry=geometry,
        spatial_geometry=geometry_from_geojson(geometry),
    )


def _activate_projection(generation: WfsGeneration) -> WfsGeneration:
    manifest = generation.manifest
    now = timezone.now()
    cadastres = {item.id: item for item in Cadastre.objects.all()}
    feature_qs = generation.features.order_by("id")
    if feature_qs.count() != generation.feature_count:
        raise ValueError("Staging feature count no longer matches the validated generation.")

    with transaction.atomic():
        manifest = WfsLayerManifest.objects.select_for_update().get(pk=manifest.pk)
        current = (
            WfsGeneration.objects.select_for_update()
            .filter(manifest=manifest, status=WfsGeneration.Status.ACTIVE)
            .exclude(pk=generation.pk)
            .first()
        )
        ForestRegistryFeature.objects.filter(source_layer=manifest.source_layer).delete()

        batch = []
        subparts: dict[str, set[int]] = defaultdict(set)
        for feature in feature_qs.iterator(chunk_size=500):
            cadastre = cadastres.get(feature.cadastre_id)
            if cadastre is None:
                raise ValueError(f"Staged cadastre {feature.cadastre_id} is no longer available.")
            batch.append(_projection_row(manifest, feature, cadastre))
            properties = feature.properties if isinstance(feature.properties, dict) else {}
            subpart_code = properties.get("eraldise_nr")
            if manifest.source_layer == "metsaregister:eraldis" and subpart_code is not None:
                try:
                    subpart_code = int(subpart_code)
                except (TypeError, ValueError):
                    subpart_code = None
                if subpart_code is not None:
                    subparts[cadastre.id].add(subpart_code)
                    CadastreSubPart.objects.update_or_create(
                        cadastre=cadastre,
                        sub_part_code=subpart_code,
                        defaults={
                            "tree_type_code": str(properties.get("peapuuliik_kood") or ""),
                            "area": _decimal(properties.get("pindala")),
                            "polygon": feature.geometry.get("coordinates", []) if isinstance(feature.geometry, dict) else [],
                            "boundary": geometry_from_geojson(feature.geometry, polygon_only=True),
                        },
                    )
            if len(batch) >= 500:
                ForestRegistryFeature.objects.bulk_create(batch, batch_size=500)
                batch = []
        if batch:
            ForestRegistryFeature.objects.bulk_create(batch, batch_size=500)

        if manifest.source_layer == "metsaregister:eraldis":
            for cadastre_id, retained_codes in subparts.items():
                CadastreSubPart.objects.filter(cadastre_id=cadastre_id).exclude(sub_part_code__in=retained_codes).delete()

        if current:
            current.status = WfsGeneration.Status.RETIRED
            current.retired_at = now
            current.save(update_fields=("status", "retired_at"))
        generation.status = WfsGeneration.Status.ACTIVE
        generation.published_at = now
        generation.retired_at = None
        generation.save(update_fields=("status", "published_at", "retired_at"))
    return generation


def publish_generation(generation: WfsGeneration) -> WfsGeneration:
    if generation.status != WfsGeneration.Status.READY:
        raise ValueError("Only a validated READY generation can be published.")
    return _activate_projection(generation)


def rollback_generation(generation: WfsGeneration) -> WfsGeneration:
    if generation.status not in (WfsGeneration.Status.RETIRED, WfsGeneration.Status.ACTIVE):
        raise ValueError("Rollback target must be an already published generation.")
    if generation.status == WfsGeneration.Status.ACTIVE:
        return generation
    return _activate_projection(generation)


def refresh_manifest(manifest: WfsLayerManifest, *, created_by=None) -> WfsGeneration:
    generation = stage_generation(manifest, created_by=created_by)
    if generation.status == WfsGeneration.Status.READY:
        return publish_generation(generation)
    return generation


def deep_verify(manifest: WfsLayerManifest) -> dict:
    active = manifest.generations.filter(status=WfsGeneration.Status.ACTIVE).first()
    if active is None:
        result = {"ok": False, "reason": "NO_ACTIVE_GENERATION"}
    else:
        fields, schema_hash = generation_schema_from_storage(active)
        staged_count = active.features.count()
        projection_count = ForestRegistryFeature.objects.filter(source_layer=manifest.source_layer).count()
        result = {
            "ok": staged_count == active.feature_count and projection_count == active.feature_count and schema_hash == active.schema_hash,
            "generationId": str(active.id),
            "stagedCount": staged_count,
            "projectionCount": projection_count,
            "expectedCount": active.feature_count,
            "schemaHash": schema_hash,
            "expectedSchemaHash": active.schema_hash,
            "schemaFields": fields,
        }
    manifest.last_verified_at = timezone.now()
    manifest.save(update_fields=("last_verified_at", "updated_at"))
    return result


def cleanup_retired_generations(manifest: WfsLayerManifest) -> int:
    keep = max(int(manifest.retention_generations), 1)
    retained_ids = list(
        manifest.generations.filter(status=WfsGeneration.Status.RETIRED)
        .order_by("-sequence")
        .values_list("id", flat=True)[:keep]
    )
    removable = manifest.generations.filter(status=WfsGeneration.Status.RETIRED)
    if retained_ids:
        removable = removable.exclude(id__in=retained_ids)
    count = removable.count()
    removable.delete()
    return count
