from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Privilege, User


class PrivilegeInline(admin.TabularInline):
    model = Privilege
    extra = 0


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "full_name", "is_staff", "is_active", "visible", "created_at")
    list_filter = ("is_staff", "is_active", "visible")
    search_fields = ("id", "full_name")
    ordering = ("id",)
    inlines = [PrivilegeInline]
    fieldsets = (
        (None, {"fields": ("id", "password")}),
        ("Profiil", {"fields": ("full_name", "totp_secret", "visible")}),
        ("Õigused", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Kuupäevad", {"fields": ("last_login", "created_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("id", "full_name", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
    readonly_fields = ("created_at", "last_login")
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Privilege)
class PrivilegeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "code")
    list_filter = ("code",)
    search_fields = ("user__id", "user__full_name", "code")
