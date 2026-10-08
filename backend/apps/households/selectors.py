from django.db.models import QuerySet

from .models import HouseholdMembership


def tenant_queryset(queryset: QuerySet, membership: HouseholdMembership) -> QuerySet:
    """The mandatory baseline for querying future household-bound models."""
    return queryset.filter(household_id=membership.household_id)
