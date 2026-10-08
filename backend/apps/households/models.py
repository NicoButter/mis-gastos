import uuid

from django.conf import settings
from django.db import models


class Household(models.Model):
    """The root tenant. Creation workflow is intentionally deferred to Phase 1."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    base_currency = models.CharField(max_length=3, default="ARS")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self) -> str:
        return self.name


class HouseholdMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Titular"
        ADMIN = "admin", "Administrador"
        MEMBER = "member", "Miembro"
        LIMITED_ENTRY = "limited_entry", "Carga limitada"

    class Status(models.TextChoices):
        ACTIVE = "active", "Activa"
        REVOKED = "revoked", "Revocada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="household_memberships"
    )
    household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="memberships")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "household"], name="unique_household_membership"
            )
        ]
        indexes = [models.Index(fields=["user", "status"], name="membership_user_status_idx")]

    def __str__(self) -> str:
        return f"{self.user_id} in {self.household_id}"
