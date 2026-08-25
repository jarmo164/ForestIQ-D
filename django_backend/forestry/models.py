"""Forest owner, cadastre and registry models."""

from __future__ import annotations

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models


class OwnerType(models.TextChoices):
    COUNTRY = "COUNTRY", "Country"
    PERSON = "PERSON", "Person"
    COMPANY = "COMPANY", "Company"


class CadastreLabelCode(models.TextChoices):
    CONSERVATION_AREA = "CONSERVATION_AREA", "Conservation area"
    DEAD_LAND = "DEAD_LAND", "Dead land"
    SWAMP = "SWAMP", "Swamp"
    REAL_ESTATE = "REAL_ESTATE", "Real estate"
    NOTIFICATIONS_CONSUMED = "NOTIFICATIONS_CONSUMED", "Notifications consumed"


class OwnerStatus(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    days_out_of_search = models.PositiveIntegerField(db_column="days_out_of_search")
    color_hex = models.CharField(max_length=6, db_column="reason_color")
    protected = models.BooleanField(default=False)

    class Meta:
        db_table = "owner_statuses"
        ordering = ("id",)

    def __str__(self) -> str:
        return self.id


class Owner(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=OwnerType.choices, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    address = models.CharField(max_length=500, blank=True)
    info = models.TextField(blank=True)
    out_of_admin_search_from = models.DateTimeField(null=True, blank=True)
    out_of_admin_search_to = models.DateTimeField(null=True, blank=True)
    out_of_admin_search_reason = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=100, blank=True)
    status_set_at = models.DateTimeField(null=True, blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_owners",
        db_column="caller_id",
    )
    last_cadastre_list_refresh = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "owners"
        ordering = ("name", "id")
        indexes = [
            models.Index(fields=("status",), name="owners_status_idx"),
            models.Index(fields=("assignee",), name="owners_assignee_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.id} — {self.name}"


class Cadastre(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=100, blank=True)
    municipality = models.CharField(max_length=50, blank=True)
    county = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=500, blank=True)
    registration_number = models.CharField(max_length=50, blank=True, db_column="reg_nr")
    type = models.CharField(max_length=100, blank=True)
    postal = models.CharField(max_length=100, blank=True)
    polygon = models.JSONField(default=list, blank=True)
    centroid = models.JSONField(default=dict, blank=True)
    boundary = gis_models.MultiPolygonField(srid=3301, null=True, blank=True)
    centroid_geometry = gis_models.PointField(srid=3301, null=True, blank=True)
    area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    arable_area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    yard_area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    meadow_area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    forest_area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    underwater_area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    buildings_area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    other_area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    marked = models.BooleanField(default=False)
    our_price = models.CharField(max_length=255, blank=True)
    owners_price = models.CharField(max_length=255, blank=True)
    mk_date = models.DateTimeField(null=True, blank=True)
    owners = models.ManyToManyField(Owner, through="OwnerCadastre", related_name="cadastres")

    class Meta:
        db_table = "cadastres"
        ordering = ("id",)
        indexes = [
            models.Index(fields=("county", "municipality"), name="cadastre_location_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.id} — {self.name}"


class OwnerCadastre(models.Model):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, db_column="owner_id")
    cadastre = models.ForeignKey(Cadastre, on_delete=models.CASCADE, db_column="cadastre_id")

    class Meta:
        db_table = "owner_cadastre"
        constraints = [models.UniqueConstraint(fields=("owner", "cadastre"), name="unique_owner_cadastre")]


class OwnerLog(models.Model):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="logs", db_column="owner_id")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owner_logs",
        db_column="creator",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_column="timestamp")

    class Meta:
        db_table = "owner_log"
        ordering = ("-created_at", "-id")


class CadastreLabel(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="pk")
    cadastre = models.ForeignKey(Cadastre, on_delete=models.CASCADE, related_name="labels", db_column="cadastre_id")
    code = models.CharField(max_length=100, choices=CadastreLabelCode.choices, db_column="id")

    class Meta:
        db_table = "cadastre_labels"
        constraints = [models.UniqueConstraint(fields=("cadastre", "code"), name="unique_cadastre_label")]


class OwnerStatusChange(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    timestamp = models.DateTimeField(auto_now_add=True)
    from_status = models.CharField(max_length=100, blank=True)
    to_status = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "user_owner_status_change_statistics"
        ordering = ("-timestamp",)


class CadastreSubPart(models.Model):
    cadastre = models.ForeignKey(Cadastre, on_delete=models.CASCADE, related_name="sub_parts", db_column="cadastre_id")
    sub_part_code = models.IntegerField(null=True, blank=True)
    tree_type_code = models.CharField(max_length=20, blank=True)
    area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    polygon = models.JSONField(default=list, blank=True)
    boundary = gis_models.MultiPolygonField(srid=3301, null=True, blank=True)

    class Meta:
        db_table = "cadastre_sub_parts"
        constraints = [models.UniqueConstraint(fields=("cadastre", "sub_part_code"), name="unique_cadastre_subpart")]


class CadastreNotification(models.Model):
    id = models.BigIntegerField(primary_key=True)
    notification_number = models.BigIntegerField()
    cadastre_subpart_code = models.IntegerField(null=True, blank=True)
    work_code = models.CharField(max_length=20, blank=True)
    state = models.IntegerField(null=True, blank=True)
    damage_code = models.CharField(max_length=20, blank=True)
    decision = models.CharField(max_length=20, blank=True)
    registration_date = models.DateTimeField(null=True, blank=True)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    amount_to_be_cut = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    cadastre = models.ForeignKey(Cadastre, on_delete=models.CASCADE, related_name="notifications", db_column="cadastre_id")
    archived = models.BooleanField(default=False)
    archive_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cadastre_notifications"
        ordering = ("-registration_date", "-id")
        indexes = [models.Index(fields=("cadastre", "archived"), name="notification_archive_idx")]


class ForestRegistryFeature(models.Model):
    source_layer = models.CharField(max_length=100)
    source_id = models.CharField(max_length=100)
    cadastre = models.ForeignKey(Cadastre, on_delete=models.CASCADE, related_name="registry_features", db_column="cadastre_id")
    subpart_code = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    work_code = models.CharField(max_length=50, blank=True)
    decision = models.CharField(max_length=100, blank=True)
    area = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    volume = models.DecimalField(max_digits=16, decimal_places=4, null=True, blank=True)
    event_date = models.DateTimeField(null=True, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    geometry = models.JSONField(default=dict, blank=True)
    spatial_geometry = gis_models.GeometryField(srid=3301, null=True, blank=True)

    class Meta:
        db_table = "forest_registry_features"
        constraints = [models.UniqueConstraint(fields=("source_layer", "source_id"), name="unique_registry_source")]
        indexes = [models.Index(fields=("cadastre", "source_layer"), name="registry_cadastre_layer_idx")]


class OwnerFollowing(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column="user_id")
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="followings", db_column="owner_id")

    class Meta:
        db_table = "owner_followings"
        constraints = [models.UniqueConstraint(fields=("owner", "user"), name="unique_owner_follower")]


class LastOwnersCadastresUpdate(models.Model):
    event_time = models.DateTimeField()

    class Meta:
        db_table = "last_owners_cadastres_update"
        ordering = ("-event_time",)


class DataSyncRun(models.Model):
    """Auditable lifecycle of one externally sourced data refresh."""

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"

    id = models.BigAutoField(primary_key=True)
    cadastre = models.ForeignKey(
        Cadastre,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sync_runs",
        db_column="cadastre_id",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requested_sync_runs",
        db_column="requested_by",
    )
    task_id = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=100, default="all")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "data_sync_runs"
        ordering = ("-id",)
        indexes = [models.Index(fields=("cadastre", "status"), name="sync_run_cadastre_status_idx")]


class InheritanceSignal(models.Model):
    """Read-only notice projection received from the authorised Pärimus API."""

    source_notice_number = models.CharField(max_length=64)
    owner = models.ForeignKey(Owner, null=True, blank=True, on_delete=models.SET_NULL, related_name="inheritance_signals")
    cadastre = models.ForeignKey(Cadastre, null=True, blank=True, on_delete=models.SET_NULL, related_name="inheritance_signals")
    announcement_date = models.DateField(null=True, blank=True)
    certification_deadline = models.DateField(null=True, blank=True)
    deceased_name = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inheritance_signals"
        ordering = ("-announcement_date", "-id")
        constraints = [models.UniqueConstraint(fields=("source_notice_number", "cadastre"), name="unique_inheritance_notice_cadastre")]
        indexes = [models.Index(fields=("owner", "announcement_date"), name="inheritance_owner_date_idx")]
