from django.contrib import admin

from .models import (
    ApplicationMessage,
    Contract,
    ContractHistory,
    DirectMessage,
    PersonDump,
    Reminder,
)


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "creator", "due_time", "created_time")
    search_fields = ("text", "owner__id", "owner__name", "cadastre", "property_name")
    autocomplete_fields = ("owner", "creator")
    readonly_fields = ("created_time",)


@admin.register(ApplicationMessage)
class ApplicationMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "admin_message", "created_at")
    list_filter = ("admin_message",)
    search_fields = ("text", "recipient__id", "recipient__full_name")
    autocomplete_fields = ("recipient",)
    readonly_fields = ("created_at",)


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "recipient", "created_at", "noticed_at")
    search_fields = ("text", "sender__id", "recipient__id")
    autocomplete_fields = ("sender", "recipient")
    readonly_fields = ("created_at",)


@admin.register(PersonDump)
class PersonDumpAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "phone", "source")
    search_fields = ("name", "code", "phone", "address", "source")


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("id", "base_id")
    search_fields = ("id", "base_id")
    exclude = ("document",)


@admin.register(ContractHistory)
class ContractHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "contract_number", "buyer", "created_at")
    search_fields = ("id", "contract_number", "buyer", "sellers", "cadastres")
    readonly_fields = ("created_at",)
