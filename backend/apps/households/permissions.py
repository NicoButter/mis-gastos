from rest_framework.permissions import BasePermission

from .services import require_household_permission, resolve_active_membership


class HasHouseholdPermission(BasePermission):
    """Base permission for future nested household API endpoints."""

    required_permission: str | None = None

    def has_permission(self, request, view):
        household_id = view.kwargs.get("household_id")
        if household_id is None:
            return False
        membership = resolve_active_membership(request.user, household_id)
        permission = getattr(view, "household_permission", self.required_permission)
        if permission:
            require_household_permission(membership, permission)
        request.household_membership = membership
        return True
