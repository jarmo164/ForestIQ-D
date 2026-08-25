from django.contrib.gis.db import models as gis_models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("forestry", "0002_datasyncrun_inheritancesignal")]

    operations = [
        migrations.AddField(model_name="cadastre", name="boundary", field=gis_models.MultiPolygonField(blank=True, null=True, srid=3301)),
        migrations.AddField(model_name="cadastre", name="centroid_geometry", field=gis_models.PointField(blank=True, null=True, srid=3301)),
        migrations.AddField(model_name="cadastresubpart", name="boundary", field=gis_models.MultiPolygonField(blank=True, null=True, srid=3301)),
        migrations.AddField(model_name="forestregistryfeature", name="spatial_geometry", field=gis_models.GeometryField(blank=True, null=True, srid=3301)),
    ]
