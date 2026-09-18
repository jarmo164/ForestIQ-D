from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import uuid
import accounts.models


class Migration(migrations.Migration):
    dependencies = [
        ("forestry", "0011_add_gis_summary_indexes"),
    ]

    operations = [
        migrations.CreateModel(
            name="BasemapDefinition",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("key", models.SlugField(max_length=80)),
                ("name", models.CharField(max_length=160)),
                ("tile_url_template", models.URLField(max_length=1000)),
                ("attribution", models.CharField(blank=True, max_length=500)),
                ("enabled", models.BooleanField(default=True)),
                ("max_zoom", models.PositiveSmallIntegerField(default=19)),
                ("cache_seconds", models.PositiveIntegerField(default=3600)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "p3_basemap_definitions", "ordering": ("key",)},
        ),
        migrations.CreateModel(
            name="ExternalMapLayer",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("key", models.SlugField(max_length=80)),
                ("name", models.CharField(max_length=160)),
                ("service_type", models.CharField(choices=[("WMS", "WMS"), ("MVT", "MVT")], max_length=10)),
                ("url_template", models.URLField(max_length=1500)),
                ("source_layer", models.CharField(blank=True, max_length=160)),
                ("visible", models.BooleanField(default=False)),
                ("opacity", models.DecimalField(decimal_places=3, default=0.75, max_digits=4)),
                ("usage_rights", models.TextField(blank=True)),
                ("attribution", models.CharField(blank=True, max_length=500)),
                ("freshness_at", models.DateTimeField(blank=True, null=True)),
                ("min_zoom", models.PositiveSmallIntegerField(default=0)),
                ("max_zoom", models.PositiveSmallIntegerField(default=22)),
                ("cache_seconds", models.PositiveIntegerField(default=300)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "p3_external_map_layers", "ordering": ("name", "key")},
        ),
        migrations.AddConstraint(
            model_name="basemapdefinition",
            constraint=models.UniqueConstraint(fields=("organization", "key"), name="p3_uq_basemap_key"),
        ),
        migrations.AddConstraint(
            model_name="externalmaplayer",
            constraint=models.UniqueConstraint(fields=("organization", "key"), name="p3_uq_external_layer_key"),
        ),
        migrations.AlterModelManagers(
            name="basemapdefinition",
            managers=[("objects", django.db.models.manager.Manager()), ("all_objects", django.db.models.manager.Manager())],
        ),
        migrations.AlterModelManagers(
            name="externalmaplayer",
            managers=[("objects", django.db.models.manager.Manager()), ("all_objects", django.db.models.manager.Manager())],
        ),
    ]
