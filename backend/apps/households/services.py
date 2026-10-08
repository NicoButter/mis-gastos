from __future__ import annotations

from uuid import UUID

from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import NotAuthenticated, NotFound, PermissionDenied, ValidationError

from .models import HouseholdMembership


def resolve_active_membership(user, household_id: str | UUID) -> HouseholdMembership:
    """Resolve tenant context server-side before querying tenant-bound objects."""
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        raise NotAuthenticated("Se requiere autenticación.")
    try:
        tenant_id = UUID(str(household_id))
    except (TypeError, ValueError) as exc:
        raise ValidationError({"household_id": ["Identificador de hogar inválido."]}) from exc
    try:
        return HouseholdMembership.objects.select_related("household").get(
            user=user, household_id=tenant_id, status=HouseholdMembership.Status.ACTIVE
        )
    except HouseholdMembership.DoesNotExist as exc:
        # A 404 reduces tenant enumeration.
        raise NotFound("Recurso no encontrado.") from exc


ROLE_PERMISSIONS = {
    HouseholdMembership.Role.OWNER: {
        "household.manage",
        "member.manage",
        "transaction.create",
        "reports.view",
    },
    HouseholdMembership.Role.ADMIN: {
        "household.manage",
        "member.manage",
        "transaction.create",
        "reports.view",
    },
    HouseholdMembership.Role.MEMBER: {"transaction.create", "reports.view"},
    HouseholdMembership.Role.LIMITED_ENTRY: {"transaction.create"},
}


def require_household_permission(membership: HouseholdMembership, permission: str) -> None:
    if permission not in ROLE_PERMISSIONS.get(membership.role, set()):
        raise PermissionDenied("No tiene permiso para esta operación.")
