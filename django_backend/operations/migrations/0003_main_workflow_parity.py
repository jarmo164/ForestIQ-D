import django.db.models.deletion
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("forestry", "0003_postgis_geometry_fields"), ("operations", "0002_contract_local_file")]

    operations = [
        migrations.CreateModel(
            name="Deal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("sale_subject", models.CharField(choices=[("FOREST", "Forest"), ("LAND", "Land"), ("BOTH", "Both")], max_length=10)),
                ("stage", models.CharField(choices=[("QUALIFICATION", "Qualification"), ("EVALUATION", "Evaluation"), ("NEGOTIATION", "Negotiation"), ("WON", "Won"), ("LOST", "Lost"), ("CANCELLED", "Cancelled")], default="QUALIFICATION", max_length=20)),
                ("decision_maker", models.CharField(blank=True, max_length=200)),
                ("sale_timeframe", models.CharField(blank=True, max_length=200)),
                ("price_expectation", models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ("qualification_notes", models.TextField(blank=True)),
                ("evaluation_status", models.CharField(blank=True, max_length=20)),
                ("estimated_min_price", models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ("estimated_max_price", models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ("recommended_purchase_price", models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ("internal_min_price", models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ("proposed_offer_price", models.DecimalField(blank=True, decimal_places=2, max_digits=16, null=True)),
                ("offer_valid_until", models.DateField(blank=True, null=True)),
                ("evaluation_assumptions", models.TextField(blank=True)), ("evaluation_risks", models.TextField(blank=True)), ("returned_reason", models.TextField(blank=True)), ("loss_reason", models.CharField(blank=True, max_length=100)),
                ("closed_at", models.DateTimeField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_deals", to=settings.AUTH_USER_MODEL)),
                ("evaluator", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="evaluated_deals", to=settings.AUTH_USER_MODEL)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deals", to="forestry.owner")),
                ("parcels", models.ManyToManyField(related_name="deals", to="forestry.cadastre")),
            ], options={"db_table": "commercial_deals", "ordering": ("-updated_at",)},
        ),
        migrations.AddIndex(model_name="deal", index=models.Index(fields=["owner", "stage"], name="deal_owner_stage_idx")),
        migrations.AddIndex(model_name="deal", index=models.Index(fields=["stage", "updated_at"], name="deal_stage_updated_idx")),
        migrations.CreateModel(
            name="DealOffer",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("revision", models.PositiveIntegerField()),
                ("kind", models.CharField(choices=[("OFFER", "Offer"), ("COUNTEROFFER", "Counteroffer")], max_length=20)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("SENT", "Sent"), ("ACCEPTED", "Accepted"), ("REJECTED", "Rejected"), ("CANCELLED", "Cancelled")], default="DRAFT", max_length=20)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=16)), ("valid_until", models.DateField(blank=True, null=True)), ("terms", models.TextField(blank=True)), ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("sent_at", models.DateTimeField(blank=True, null=True)), ("accepted_at", models.DateTimeField(blank=True, null=True)), ("rejected_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_deal_offers", to=settings.AUTH_USER_MODEL)),
                ("deal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="offers", to="operations.deal")),
            ], options={"db_table": "commercial_deal_offers", "ordering": ("revision", "created_at")},
        ),
        migrations.AddConstraint(model_name="dealoffer", constraint=models.UniqueConstraint(fields=("deal", "revision"), name="unique_deal_offer_revision")),
        migrations.CreateModel(
            name="InheritanceCase",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("source_notice_number", models.CharField(blank=True, max_length=64)), ("source_url", models.URLField(blank=True, max_length=500)),
                ("announcement_date", models.DateField(blank=True, null=True)), ("death_date", models.DateField(blank=True, null=True)), ("certification_deadline", models.DateField(blank=True, null=True)), ("notary_name", models.CharField(blank=True, max_length=255)), ("notary_phone", models.CharField(blank=True, max_length=100)),
                ("status", models.CharField(choices=[("NEW", "New"), ("IN_PROGRESS", "In progress"), ("WAITING", "Waiting"), ("COMPLETED", "Completed"), ("CLOSED", "Closed")], default="NEW", max_length=20)), ("started_at", models.DateTimeField(auto_now_add=True)), ("ended_at", models.DateTimeField(blank=True, null=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_inheritance_cases", to=settings.AUTH_USER_MODEL)), ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inheritance_cases", to="forestry.owner")),
            ], options={"db_table": "inheritance_cases", "ordering": ("-updated_at",)},
        ),
        migrations.AddIndex(model_name="inheritancecase", index=models.Index(fields=["status", "assigned_to"], name="inherit_case_status_idx")),
        migrations.CreateModel(
            name="InheritanceHeir",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("display_name", models.CharField(max_length=255)), ("personal_code", models.CharField(blank=True, max_length=50)), ("registry_code", models.CharField(blank=True, max_length=50)), ("inheritance_share", models.CharField(blank=True, max_length=100)), ("relation_to_deceased", models.CharField(blank=True, max_length=100)), ("phone", models.CharField(blank=True, max_length=100)), ("email", models.EmailField(blank=True, max_length=254)), ("contact_status", models.CharField(blank=True, max_length=100)), ("source", models.CharField(blank=True, max_length=100)),
                ("assigned_to", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_inheritance_heirs", to=settings.AUTH_USER_MODEL)), ("inheritance_case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="heirs", to="operations.inheritancecase")),
            ], options={"db_table": "inheritance_heirs", "ordering": ("display_name",)},
        ),
        migrations.CreateModel(
            name="InheritanceCaseEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("type", models.CharField(max_length=100)), ("description", models.TextField()), ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inheritance_events", to=settings.AUTH_USER_MODEL)), ("inheritance_case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="operations.inheritancecase")),
            ], options={"db_table": "inheritance_case_events", "ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="OwnerImportBatch",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("filename", models.CharField(max_length=255)), ("sha256", models.CharField(max_length=64)), ("created_count", models.PositiveIntegerField(default=0)), ("rejected_rows", models.JSONField(blank=True, default=list)), ("committed_at", models.DateTimeField(auto_now_add=True)),
                ("creator", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="owner_import_batches", to=settings.AUTH_USER_MODEL)),
            ], options={"db_table": "owner_import_batches", "ordering": ("-committed_at",)},
        ),
        migrations.CreateModel(
            name="OwnershipTransitionEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("event_type", models.CharField(max_length=100)), ("occurred_at", models.DateTimeField(blank=True, null=True)), ("source_reference", models.CharField(blank=True, max_length=255)), ("payload", models.JSONField(blank=True, default=dict)), ("recorded_at", models.DateTimeField(auto_now_add=True)),
                ("cadastre", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ownership_transitions", to="forestry.cadastre")), ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ownership_transitions", to="forestry.owner")),
            ], options={"db_table": "ownership_transition_events", "ordering": ("-occurred_at", "-recorded_at")},
        ),
        migrations.AddIndex(model_name="ownershiptransitionevent", index=models.Index(fields=["owner", "occurred_at"], name="ownership_owner_date_idx")),
    ]
