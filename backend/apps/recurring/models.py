import uuid

from django.conf import settings
from django.db import models


class RecurringExpense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    category = models.ForeignKey("categories.Category", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    start_date = models.DateField()
    resume_date = models.DateField(null=True, blank=True)
    due_day = models.PositiveSmallIntegerField()
    account = models.ForeignKey(
        "wallets.FinancialAccount", on_delete=models.PROTECT, null=True, blank=True
    )
    status = models.CharField(
        max_length=10,
        default="active",
        choices=[("active", "Activa"), ("paused", "Pausada"), ("cancelled", "Cancelada")],
    )

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    amount__gt=0,
                    due_day__gte=1,
                    due_day__lte=31,
                    status__in=["active", "paused", "cancelled"],
                ),
                name="recurring_valid_rule",
            )
        ]


class RecurringOccurrence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    recurring = models.ForeignKey(
        RecurringExpense, on_delete=models.PROTECT, related_name="occurrences"
    )
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(
        max_length=10,
        default="pending",
        choices=[("pending", "Pendiente"), ("paid", "Pagada"), ("cancelled", "Cancelada")],
    )
    payment = models.OneToOneField(
        "transactions.FinancialTransaction",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="recurring_occurrence",
    )

    class Meta:
        ordering = ["due_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["recurring", "due_date"], name="single_recurring_occurrence"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0)
                & (
                    models.Q(status="paid", payment__isnull=False)
                    | models.Q(status__in=["pending", "cancelled"], payment__isnull=True)
                ),
                name="recurring_valid_occurrence",
            ),
        ]
        indexes = [models.Index(fields=["household", "due_date"])]
