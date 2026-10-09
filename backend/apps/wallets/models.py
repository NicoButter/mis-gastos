import uuid

from django.db import models


class FinancialAccount(models.Model):
    class Kind(models.TextChoices):
        CASH = "cash", "Efectivo"
        BANK = "bank", "Banco"
        WALLET = "wallet", "Billetera virtual"
        OTHER = "other", "Otra cuenta"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    currency = models.CharField(max_length=3, default="ARS")
    description = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(currency="ARS"), name="account_ars_only"),
            models.CheckConstraint(
                condition=models.Q(kind__in=["cash", "bank", "wallet", "other"]),
                name="account_valid_kind",
            ),
        ]
        indexes = [models.Index(fields=["household", "is_active"])]
