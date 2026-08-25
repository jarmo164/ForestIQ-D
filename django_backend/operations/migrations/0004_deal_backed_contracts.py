from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("operations", "0003_main_workflow_parity")]

    operations = [
        migrations.AddField(model_name="contract", name="source_deal", field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="contracts", to="operations.deal")),
        migrations.AddField(model_name="contract", name="source_offer", field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="contracts", to="operations.dealoffer")),
    ]
