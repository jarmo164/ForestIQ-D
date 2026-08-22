# Generated manually for the ForestIQ external data synchronisation models.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("forestry", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DataSyncRun",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("task_id", models.CharField(blank=True, max_length=100)),
                ("source", models.CharField(default="all", max_length=100)),
                ("status", models.CharField(choices=[("QUEUED", "Queued"), ("RUNNING", "Running"), ("SUCCEEDED", "Succeeded"), ("FAILED", "Failed")], default="QUEUED", max_length=20)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("cadastre", models.ForeignKey(blank=True, db_column="cadastre_id", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sync_runs", to="forestry.cadastre")),
                ("requested_by", models.ForeignKey(blank=True, db_column="requested_by", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="requested_sync_runs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "data_sync_runs", "ordering": ("-id",)},
        ),
        migrations.AddIndex(model_name="datasyncrun", index=models.Index(fields=["cadastre", "status"], name="sync_run_cadastre_status_idx")),
        migrations.CreateModel(
            name="InheritanceSignal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_notice_number", models.CharField(max_length=64)),
                ("announcement_date", models.DateField(blank=True, null=True)),
                ("certification_deadline", models.DateField(blank=True, null=True)),
                ("deceased_name", models.CharField(blank=True, max_length=255)),
                ("source_url", models.URLField(blank=True, max_length=500)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("fetched_at", models.DateTimeField(auto_now=True)),
                ("cadastre", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inheritance_signals", to="forestry.cadastre")),
                ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inheritance_signals", to="forestry.owner")),
            ],
            options={"db_table": "inheritance_signals", "ordering": ("-announcement_date", "-id")},
        ),
        migrations.AddConstraint(model_name="inheritancesignal", constraint=models.UniqueConstraint(fields=("source_notice_number", "cadastre"), name="unique_inheritance_notice_cadastre")),
        migrations.AddIndex(model_name="inheritancesignal", index=models.Index(fields=["owner", "announcement_date"], name="inheritance_owner_date_idx")),
    ]
