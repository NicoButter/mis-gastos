import uuid

from django.conf import settings
from django.db import models


class FinancialTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    type = models.CharField(
        max_length=10,
        choices=[
            ("opening", "Apertura"),
            ("income", "Ingreso"),
            ("expense", "Gasto"),
            ("transfer", "Transferencia"),
        ],
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default="ARS")
    effective_date = models.DateField()
    description = models.CharField(max_length=500, blank=True)
    account = models.ForeignKey(
        "wallets.FinancialAccount", on_delete=models.PROTECT, related_name="operations"
    )
    destination = models.ForeignKey(
        "wallets.FinancialAccount",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="incoming_transfers",
    )
    category = models.ForeignKey(
        "categories.Category", on_delete=models.PROTECT, null=True, blank=True
    )
    status = models.CharField(
        max_length=10, default="posted", choices=[("posted", "Vigente"), ("voided", "Anulado")]
    )
    revision = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-effective_date", "-created_at", "-id"]
        indexes = [models.Index(fields=["household", "effective_date", "id"])]
        constraints = [
            models.UniqueConstraint(
                fields=["account"],
                condition=models.Q(type="opening"),
                name="single_account_opening",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="operation_positive_amount"
            ),
            models.CheckConstraint(condition=models.Q(currency="ARS"), name="operation_ars_only"),
            models.CheckConstraint(
                condition=models.Q(status__in=["posted", "voided"]), name="operation_valid_status"
            ),
            models.CheckConstraint(
                condition=models.Q(revision__gte=1), name="operation_positive_revision"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        type__in=["income", "expense"],
                        category__isnull=False,
                        destination__isnull=True,
                    )
                    | models.Q(type="opening", category__isnull=True, destination__isnull=True)
                    | (
                        models.Q(type="transfer", category__isnull=True, destination__isnull=False)
                        & ~models.Q(account=models.F("destination"))
                    )
                ),
                name="operation_valid_shape",
            ),
        ]


class LedgerEntry(models.Model):
    """Immutable revision entries; only the current posted revision affects balances."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    transaction = models.ForeignKey(
        FinancialTransaction, on_delete=models.PROTECT, related_name="entries"
    )
    account = models.ForeignKey(
        "wallets.FinancialAccount", on_delete=models.PROTECT, related_name="entries"
    )
    revision = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["transaction", "revision", "account"], name="ledger_revision_account"
            ),
            models.CheckConstraint(condition=~models.Q(amount=0), name="ledger_nonzero"),
        ]
        indexes = [models.Index(fields=["household", "account"])]


class WriteReceipt(models.Model):
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household", "actor", "key"], name="financial_write_key"
            )
        ]
