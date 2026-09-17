from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid
import accounts.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("operations", "0012_p1_model_managers"),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionEvidenceSnapshot",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("sequence", models.PositiveIntegerField()),
                ("decision_type", models.CharField(choices=[("EVALUATION", "Evaluation"), ("OFFER", "Offer")], default="EVALUATION", max_length=20)),
                ("schema_version", models.PositiveSmallIntegerField(default=1)),
                ("snapshot", models.JSONField(default=dict)),
                ("snapshot_sha256", models.CharField(max_length=64)),
                ("confirmed_at", models.DateTimeField(auto_now_add=True)),
                ("confirmed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="confirmed_decision_evidence_snapshots", to=settings.AUTH_USER_MODEL)),
                ("deal", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decision_evidence_snapshots", to="operations.deal")),
            ],
            options={
                "db_table": "p2_decision_evidence_snapshots",
                "ordering": ("deal_id", "-sequence"),
            },
        ),
        migrations.AddIndex(
            model_name="decisionevidencesnapshot",
            index=models.Index(fields=["organization", "deal", "confirmed_at"], name="p2_decision_snapshot_deal_idx"),
        ),
        migrations.AddConstraint(
            model_name="decisionevidencesnapshot",
            constraint=models.UniqueConstraint(fields=("organization", "deal", "sequence"), name="p2_uq_decision_snapshot_sequence"),
        ),
    ]
