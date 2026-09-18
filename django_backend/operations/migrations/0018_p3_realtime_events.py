from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import uuid
import accounts.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("operations", "0017_p3_notification_preferences"),
    ]

    operations = [
        migrations.CreateModel(
            name="RealtimeEvent",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=100)),
                ("topic", models.CharField(default="organization", max_length=100)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="emitted_realtime_events", to=settings.AUTH_USER_MODEL)),
                ("recipient", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="realtime_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "p3_realtime_events", "ordering": ("-created_at", "-id")},
        ),
        migrations.AddIndex(
            model_name="realtimeevent",
            index=models.Index(fields=["organization", "created_at"], name="p3_realtime_org_time_idx"),
        ),
        migrations.AddIndex(
            model_name="realtimeevent",
            index=models.Index(fields=["organization", "recipient", "created_at"], name="p3_realtime_user_time_idx"),
        ),
        migrations.AlterModelManagers(
            name="realtimeevent",
            managers=[("objects", django.db.models.manager.Manager()), ("all_objects", django.db.models.manager.Manager())],
        ),
    ]
