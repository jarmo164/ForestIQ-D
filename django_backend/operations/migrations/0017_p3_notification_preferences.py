from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import uuid
import accounts.models
import operations.p3_models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("operations", "0016_sales_funnel_segments"),
    ]

    operations = [
        migrations.AddField(
            model_name="applicationmessage",
            name="read_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="applicationmessage",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="applicationmessage",
            name="category",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="applicationmessage",
            name="event_key",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_preferences", to=settings.AUTH_USER_MODEL)),
                ("enabled", models.BooleanField(default=True)),
                ("event_types", models.JSONField(default=operations.p3_models.default_notification_events)),
                ("channels", models.JSONField(default=operations.p3_models.default_notification_channels)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "p3_notification_preferences"},
        ),
        migrations.AddConstraint(
            model_name="notificationpreference",
            constraint=models.UniqueConstraint(fields=("organization", "user"), name="p3_uq_notification_preference_user"),
        ),
        migrations.CreateModel(
            name="ReminderNotificationDelivery",
            fields=[
                ("organization", models.ForeignKey(default=accounts.models.default_organization_id, on_delete=django.db.models.deletion.CASCADE, related_name="+", to="accounts.organization")),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("channel", models.CharField(default="IN_APP", max_length=20)),
                ("status", models.CharField(choices=[("SENT", "Sent"), ("SKIPPED", "Skipped")], default="SENT", max_length=20)),
                ("reason", models.CharField(blank=True, max_length=255)),
                ("dispatched_at", models.DateTimeField(auto_now_add=True)),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reminder_notification_deliveries", to=settings.AUTH_USER_MODEL)),
                ("reminder", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_deliveries", to="operations.reminder")),
            ],
            options={"db_table": "p3_reminder_notification_deliveries"},
        ),
        migrations.AddConstraint(
            model_name="remindernotificationdelivery",
            constraint=models.UniqueConstraint(fields=("organization", "reminder", "recipient", "channel"), name="p3_uq_reminder_notification_delivery"),
        ),
        migrations.AddIndex(
            model_name="remindernotificationdelivery",
            index=models.Index(fields=["organization", "recipient", "dispatched_at"], name="p3_reminder_delivery_user_idx"),
        ),
        migrations.AlterModelManagers(
            name="notificationpreference",
            managers=[("objects", django.db.models.manager.Manager()), ("all_objects", django.db.models.manager.Manager())],
        ),
        migrations.AlterModelManagers(
            name="remindernotificationdelivery",
            managers=[("objects", django.db.models.manager.Manager()), ("all_objects", django.db.models.manager.Manager())],
        ),
    ]
