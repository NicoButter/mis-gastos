from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class GastioUserAdmin(UserAdmin):
    model = User
    ordering = ("email",)
    list_display = ("email", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Mis Gastos", {"fields": ("locale",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Mis Gastos", {"fields": ("email", "locale")}),)
    search_fields = ("email",)
