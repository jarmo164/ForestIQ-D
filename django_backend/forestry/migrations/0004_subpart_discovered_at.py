from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("forestry", "0003_postgis_geometry_fields")]

    operations = [
        migrations.AddField(
            model_name="cadastresubpart",
            name="discovered_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
