from django.contrib import admin

from .models import (
    Cadastre,
    CadastreLabel,
    CadastreNotification,
    CadastreSubPart,
    DataSyncRun,
    ForestRegistryFeature,
    InheritanceSignal,
    LastOwnersCadastresUpdate,
    Owner,
    OwnerCadastre,
    OwnerFollowing,
    OwnerLog,
    OwnerStatus,
    OwnerStatusChange,
)


class OwnerCadastreInline(admin.TabularInline):
    model = OwnerCadastre
    extra = 0
    autocomplete_fields = ("cadastre",)


class CadastreLabelInline(admin.TabularInline):
    model = CadastreLabel
    extra = 0


@admin.register(OwnerStatus)
class OwnerStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "days_out_of_search", "color_hex", "protected")
    search_fields = ("id",)


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "status", "assignee", "phone", "email")
    list_filter = ("type", "status")
    search_fields = ("id", "name", "phone", "email", "address")
    autocomplete_fields = ("assignee",)
    inlines = [OwnerCadastreInline]


@admin.register(Cadastre)
class CadastreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "county", "municipality", "area", "forest_area", "marked")
    list_filter = ("county", "municipality", "marked")
    search_fields = ("id", "name", "address", "registration_number")
    inlines = [CadastreLabelInline]


@admin.register(OwnerCadastre)
class OwnerCadastreAdmin(admin.ModelAdmin):
    list_display = ("owner", "cadastre")
    search_fields = ("owner__id", "owner__name", "cadastre__id", "cadastre__name")
    autocomplete_fields = ("owner", "cadastre")


@admin.register(OwnerLog)
class OwnerLogAdmin(admin.ModelAdmin):
    list_display = ("owner", "creator", "created_at")
    search_fields = ("owner__id", "owner__name", "message")
    autocomplete_fields = ("owner", "creator")
    readonly_fields = ("created_at",)


@admin.register(CadastreLabel)
class CadastreLabelAdmin(admin.ModelAdmin):
    list_display = ("cadastre", "code")
    list_filter = ("code",)
    search_fields = ("cadastre__id", "cadastre__name")
    autocomplete_fields = ("cadastre",)


@admin.register(OwnerStatusChange)
class OwnerStatusChangeAdmin(admin.ModelAdmin):
    list_display = ("user", "from_status", "to_status", "timestamp")
    list_filter = ("from_status", "to_status")
    search_fields = ("user__id", "user__full_name")
    autocomplete_fields = ("user",)
    readonly_fields = ("timestamp",)


@admin.register(CadastreSubPart)
class CadastreSubPartAdmin(admin.ModelAdmin):
    list_display = ("cadastre", "sub_part_code", "tree_type_code", "area")
    search_fields = ("cadastre__id", "tree_type_code")
    autocomplete_fields = ("cadastre",)


@admin.register(CadastreNotification)
class CadastreNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "cadastre", "notification_number", "work_code", "state", "registration_date", "archived")
    list_filter = ("archived", "work_code", "state")
    search_fields = ("cadastre__id", "notification_number", "work_code")
    autocomplete_fields = ("cadastre",)


@admin.register(ForestRegistryFeature)
class ForestRegistryFeatureAdmin(admin.ModelAdmin):
    list_display = ("source_layer", "source_id", "cadastre", "title", "work_code", "event_date")
    list_filter = ("source_layer",)
    search_fields = ("source_id", "cadastre__id", "title")
    autocomplete_fields = ("cadastre",)


@admin.register(OwnerFollowing)
class OwnerFollowingAdmin(admin.ModelAdmin):
    list_display = ("user", "owner")
    search_fields = ("user__id", "owner__id", "owner__name")
    autocomplete_fields = ("user", "owner")


@admin.register(LastOwnersCadastresUpdate)
class LastOwnersCadastresUpdateAdmin(admin.ModelAdmin):
    list_display = ("id", "event_time")
    ordering = ("-event_time",)


@admin.register(DataSyncRun)
class DataSyncRunAdmin(admin.ModelAdmin):
    list_display = ("id", "cadastre", "source", "status", "requested_by", "started_at", "finished_at")
    list_filter = ("status", "source")
    search_fields = ("cadastre__id", "task_id", "error_message")
    autocomplete_fields = ("cadastre", "requested_by")
    readonly_fields = ("started_at", "finished_at")


@admin.register(InheritanceSignal)
class InheritanceSignalAdmin(admin.ModelAdmin):
    list_display = ("source_notice_number", "owner", "cadastre", "deceased_name", "announcement_date", "fetched_at")
    search_fields = ("source_notice_number", "deceased_name", "owner__id", "cadastre__id")
    autocomplete_fields = ("owner", "cadastre")
    readonly_fields = ("fetched_at",)
