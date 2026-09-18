"""P3 forestry platform-control models for managed map services."""
from __future__ import annotations

import uuid

from django.db import models

from accounts.models import OrganizationScopedModel


class BasemapDefinition(OrganizationScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.SlugField(max_length=80)
    name = models.CharField(max_length=160)
    tile_url_template = models.URLField(max_length=1000)
    attribution = models.CharField(max_length=500, blank=True)
    enabled = models.BooleanField(default=True)
    max_zoom = models.PositiveSmallIntegerField(default=19)
    cache_seconds = models.PositiveIntegerField(default=3600)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "p3_basemap_definitions"
        ordering = ("key",)
        constraints = [
            models.UniqueConstraint(fields=("organization", "key"), name="p3_uq_basemap_key"),
        ]


class ExternalMapLayer(OrganizationScopedModel):
    class ServiceType(models.TextChoices):
        WMS = "WMS", "WMS"
        MVT = "MVT", "MVT"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.SlugField(max_length=80)
    name = models.CharField(max_length=160)
    service_type = models.CharField(max_length=10, choices=ServiceType.choices)
    url_template = models.URLField(max_length=1500)
    source_layer = models.CharField(max_length=160, blank=True)
    visible = models.BooleanField(default=False)
    opacity = models.DecimalField(max_digits=4, decimal_places=3, default=0.75)
    usage_rights = models.TextField(blank=True)
    attribution = models.CharField(max_length=500, blank=True)
    freshness_at = models.DateTimeField(null=True, blank=True)
    min_zoom = models.PositiveSmallIntegerField(default=0)
    max_zoom = models.PositiveSmallIntegerField(default=22)
    cache_seconds = models.PositiveIntegerField(default=300)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "p3_external_map_layers"
        ordering = ("name", "key")
        constraints = [
            models.UniqueConstraint(fields=("organization", "key"), name="p3_uq_external_layer_key"),
        ]


class WfsLayerManifest(OrganizationScopedModel):
    """Tenant-scoped policy for one Metsaregister WFS source layer."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.SlugField(max_length=100)
    source_layer = models.CharField(max_length=200)
    cadastre_field = models.CharField(max_length=100, default="katastri_nr")
    enabled = models.BooleanField(default=True)
    allow_schema_drift = models.BooleanField(default=False)
    expected_schema_hash = models.CharField(max_length=64, blank=True)
    expected_schema_fields = models.JSONField(default=dict, blank=True)
    retention_generations = models.PositiveSmallIntegerField(default=2)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "p3_wfs_layer_manifests"
        ordering = ("key",)
        constraints = [
            models.UniqueConstraint(fields=("organization", "key"), name="p3_uq_wfs_manifest_key"),
            models.UniqueConstraint(fields=("organization", "source_layer"), name="p3_uq_wfs_manifest_layer"),
        ]


class WfsGeneration(OrganizationScopedModel):
    class Status(models.TextChoices):
        STAGING = "STAGING", "Staging"
        READY = "READY", "Ready"
        ACTIVE = "ACTIVE", "Active"
        RETIRED = "RETIRED", "Retired"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    manifest = models.ForeignKey(WfsLayerManifest, on_delete=models.CASCADE, related_name="generations")
    sequence = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STAGING)
    feature_count = models.PositiveBigIntegerField(default=0)
    cadastre_count = models.PositiveIntegerField(default=0)
    schema_hash = models.CharField(max_length=64, blank=True)
    schema_fields = models.JSONField(default=dict, blank=True)
    validation = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_wfs_generations",
    )
    schema_drift_approved_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_wfs_schema_drifts",
    )
    schema_drift_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    observed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)
    organization_parent_fields = ("manifest",)

    class Meta:
        db_table = "p3_wfs_generations"
        ordering = ("manifest_id", "-sequence")
        constraints = [
            models.UniqueConstraint(fields=("organization", "manifest", "sequence"), name="p3_uq_wfs_generation_sequence"),
        ]
        indexes = [
            models.Index(fields=("organization", "manifest", "status"), name="p3_wfs_generation_status_idx"),
        ]


class WfsGenerationFeature(OrganizationScopedModel):
    """Immutable raw feature captured inside a staging generation."""

    id = models.BigAutoField(primary_key=True)
    generation = models.ForeignKey(WfsGeneration, on_delete=models.CASCADE, related_name="features")
    source_id = models.CharField(max_length=255)
    cadastre_id = models.CharField(max_length=50)
    properties = models.JSONField(default=dict)
    geometry = models.JSONField(default=dict)
    organization_parent_fields = ("generation",)

    class Meta:
        db_table = "p3_wfs_generation_features"
        ordering = ("generation_id", "cadastre_id", "source_id")
        constraints = [
            models.UniqueConstraint(fields=("organization", "generation", "cadastre_id", "source_id"), name="p3_uq_wfs_generation_source"),
        ]
        indexes = [
            models.Index(fields=("organization", "generation", "cadastre_id"), name="p3_wfs_feature_cadastre_idx"),
        ]

    def __init__(self, *args, **kwargs):
        generation = kwargs.get("generation")
        super().__init__(*args, **kwargs)
        if generation is not None:
            if self.organization_id and self.organization_id != generation.organization_id:
                from django.core.exceptions import ValidationError
                raise ValidationError("WFS generation feature organization must match its generation.")
            if not self.organization_id:
                self.organization_id = generation.organization_id

    def save(self, *args, **kwargs):
        if not self._state.adding:
            from django.core.exceptions import ValidationError
            raise ValidationError("WFS generation features are immutable.")
        return super().save(*args, **kwargs)
