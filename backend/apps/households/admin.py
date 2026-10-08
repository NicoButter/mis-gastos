from django.contrib import admin

from .models import Household, HouseholdMembership


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "base_currency", "created_at")
    search_fields = ("name",)


@admin.register(HouseholdMembership)
class HouseholdMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "household", "role", "status")
    list_filter = ("role", "status")
