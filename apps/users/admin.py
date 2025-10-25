from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User
from .forms import AdminUserCreationForm, AdminUserChangeForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom email-based User model.
    """

    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    model = User

    ordering = ["id"]
    list_display = ["id", "email", "name", "is_staff", "is_active", "date_joined"]
    list_filter = ["is_staff", "is_superuser", "is_active", "groups"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("name",)}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("last_login", "date_joined")

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "name", 
                "password1", "password2", 
                "is_active", "is_staff", "is_superuser", "groups"
            ),
        }),
    )

    search_fields = ["email", "name"]
    filter_horizontal = ("groups", "user_permissions")
