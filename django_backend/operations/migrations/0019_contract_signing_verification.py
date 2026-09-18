from django.db import migrations, models


def require_legacy_reverification(apps, schema_editor):
    signing = apps.get_model("operations", "ContractSigning")
    signing.objects.filter(state="SIGNED").update(
        state="SENT_FOR_SIGNATURE",
        verification_status="NOT_SUBMITTED",
        verification_failure_reason="Legacy SIGNED state requires signature re-verification.",
    )


class Migration(migrations.Migration):
    dependencies = [("operations", "0018_p3_realtime_events")]

    operations = [
        migrations.AddField(model_name="contractsigning", name="verification_status", field=models.CharField(choices=[("NOT_SUBMITTED", "Not submitted"), ("PENDING", "Pending"), ("VERIFIED", "Verified"), ("FAILED", "Failed")], default="NOT_SUBMITTED", max_length=20)),
        migrations.AddField(model_name="contractsigning", name="document_sha256", field=models.CharField(blank=True, max_length=64)),
        migrations.AddField(model_name="contractsigning", name="verified_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="contractsigning", name="verification_reference", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="contractsigning", name="signer_metadata", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="contractsigning", name="certificate_metadata", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="contractsigning", name="verification_failure_reason", field=models.TextField(blank=True)),
        migrations.RunPython(require_legacy_reverification, migrations.RunPython.noop),
    ]
