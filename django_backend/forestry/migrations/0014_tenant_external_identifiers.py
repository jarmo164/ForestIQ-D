from django.db import migrations, models


def backfill_external_ids(apps, schema_editor):
    Owner = apps.get_model("forestry", "Owner")
    Cadastre = apps.get_model("forestry", "Cadastre")
    for model in (Owner, Cadastre):
        for row in model.objects.filter(external_id="").iterator(chunk_size=1000):
            row.external_id = row.id
            row.save(update_fields=("external_id",))


def clear_external_ids(apps, schema_editor):
    Owner = apps.get_model("forestry", "Owner")
    Cadastre = apps.get_model("forestry", "Cadastre")
    Owner.objects.update(external_id="")
    Cadastre.objects.update(external_id="")


class Migration(migrations.Migration):
    dependencies = [
        ("forestry", "0013_p3_wfs_generations"),
    ]

    operations = [
        migrations.AlterField(
            model_name="owner",
            name="id",
            field=models.CharField(max_length=96, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="cadastre",
            name="id",
            field=models.CharField(max_length=96, primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name="owner",
            name="external_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cadastre",
            name="external_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=50),
            preserve_default=False,
        ),
        migrations.RunPython(backfill_external_ids, clear_external_ids),
        migrations.AddConstraint(
            model_name="owner",
            constraint=models.UniqueConstraint(fields=("organization", "external_id"), name="unique_owner_org_external_id"),
        ),
        migrations.AddConstraint(
            model_name="cadastre",
            constraint=models.UniqueConstraint(fields=("organization", "external_id"), name="unique_cadastre_org_external_id"),
        ),
    ]
