from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("operations", "0001_initial")]

    operations = [migrations.AddField(model_name="contract", name="document_file", field=models.FileField(blank=True, null=True, upload_to="contracts/%Y/%m"))]
