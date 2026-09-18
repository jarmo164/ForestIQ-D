from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import uuid
import accounts.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("forestry", "0012_p3_managed_map_services"),
    ]

    operations = [
        migrations.CreateModel(
            name="WfsLayerManifest",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("key", models.SlugField(max_length=100)),
                ("source_layer", models.CharField(max_length=200)),
                ("cadastre_field", models.CharField(default="katastri_nr", max_length=100)),
                ("enabled", models.BooleanField(default=True)),
                ("allow_schema_drift", models.BooleanField(default=False)),
                ("expected_schema_hash", models.CharField(blank=True, max_length=64)),
                ("expected_schema_fields", models.JSONField(blank=True, default=dict)),
                ("retention_generations", models.PositiveSmallIntegerField(default=2)),
                ("last_verified_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "p3_wfs_layer_manifests", "ordering": ("key",)},
        ),
        migrations.CreateModel(
            name="WfsGeneration",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("sequence", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("STAGING", "Staging"), ("READY", "Ready"), ("ACTIVE", "Active"), ("RETIRED", "Retired"), ("FAILED", "Failed")], default="STAGING", max_length=20)),
                ("feature_count", models.PositiveBigIntegerField(default=0)),
                ("cadastre_count", models.PositiveIntegerField(default=0)),
                ("schema_hash", models.CharField(blank=True, max_length=64)),
                ("schema_fields", models.JSONField(blank=True, default=dict)),
                ("validation", models.JSONField(blank=True, default=dict)),
                ("schema_drift_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("observed_at", models.DateTimeField(blank=True, null=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("retired_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_wfs_generations", to=settings.AUTH_USER_MODEL)),
                ("manifest", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="generations", to="forestry.wfslayermanifest")),
                ("schema_drift_approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="approved_wfs_schema_drifts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "p3_wfs_generations", "ordering": ("manifest_id", "-sequence")},
        ),
        migrations.CreateModel(
            name="WfsGenerationFeature",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("source_id", models.CharField(max_length=255)),
                ("cadastre_id", models.CharField(max_length=50)),
                ("properties", models.JSONField(default=dict)),
                ("geometry", models.JSONField(default=dict)),
                ("generation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="features", to="forestry.wfsgeneration")),
            ],
            options={"db_table": "p3_wfs_generation_features", "ordering": ("generation_id", "cadastre_id", "source_id")},
        ),
        migrations.AddConstraint(model_name="wfslayermanifest", constraint=models.UniqueConstraint(fields=("organization", "key"), name="p3_uq_wfs_manifest_key")),
        migrations.AddConstraint(model_name="wfslayermanifest", constraint=models.UniqueConstraint(fields=("organization", "source_layer"), name="p3_uq_wfs_manifest_layer")),
        migrations.AddConstraint(model_name="wfsgeneration", constraint=models.UniqueConstraint(fields=("organization", "manifest", "sequence"), name="p3_uq_wfs_generation_sequence")),
        migrations.AddIndex(model_name="wfsgeneration", index=models.Index(fields=["organization", "manifest", "status"], name="p3_wfs_generation_status_idx")),
        migrations.AddConstraint(model_name="wfsgenerationfeature", constraint=models.UniqueConstraint(fields=("organization", "generation", "cadastre_id", "source_id"), name="p3_uq_wfs_generation_source")),
        migrations.AddIndex(model_name="wfsgenerationfeature", index=models.Index(fields=["organization", "generation", "cadastre_id"], name="p3_wfs_feature_cadastre_idx")),
        migrations.AlterModelManagers(name="wfslayermanifest", managers=[("objects", django.db.models.manager.Manager()), ("all_objects", django.db.models.manager.Manager())]),
        migrations.AlterModelManagers(name="wfsgeneration", managers=[("objects", django.db.models.manager.Manager()), ("all_objects", django.db.models.manager.Manager())]),
        migrations.AlterModelManagers(name="wfsgenerationfeature", managers=[("objects", django.db.models.manager.Manager()), ("all_objects", django.db.models.manager.Manager())]),
    ]
