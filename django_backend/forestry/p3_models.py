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
