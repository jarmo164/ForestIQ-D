from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import uuid
import accounts.models


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0018_p3_realtime_events"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataQualityScanRun",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("RUNNING", "Running"), ("SUCCESS", "Success"), ("FAILED", "Failed")], default="RUNNING", max_length=20)),
                ("trigger", models.CharField(default="MANUAL", max_length=30)),
                ("detected_count", models.PositiveIntegerField(default=0)),
                ("created_count", models.PositiveIntegerField(default=0)),
                ("auto_resolved_count", models.PositiveIntegerField(default=0)),
                ("processed_owner_count", models.PositiveIntegerField(default=0)),
                ("processed_deal_count", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "p1_data_quality_scan_runs", "ordering": ("-started_at", "-id")},
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("all_objects", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddIndex(
            model_name="dataqualityscanrun",
            index=models.Index(fields=["organization", "started_at"], name="p1_quality_scan_time_idx"),
        ),
    ]
