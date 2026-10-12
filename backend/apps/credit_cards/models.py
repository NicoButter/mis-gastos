import uuid

from django.conf import settings
from django.db import models


class CreditCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    bank = models.CharField(max_length=120)
    name = models.CharField(max_length=120)
    closing_day = models.PositiveSmallIntegerField()
    due_day = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    closing_day__gte=1, closing_day__lte=31, due_day__gte=1, due_day__lte=31
                ),
                name="card_valid_days",
            )
        ]


class CardPurchase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    card = models.ForeignKey(
        CreditCard, on_delete=models.PROTECT, related_name="purchases", null=True, blank=True
    )
    creditor = models.CharField(max_length=200, blank=True)
    first_due_date = models.DateField(null=True, blank=True)
    category = models.ForeignKey("categories.Category", on_delete=models.PROTECT)
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    purchase_date = models.DateField()
    installments_count = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["-purchase_date", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    amount__gt=0, installments_count__gte=1, installments_count__lte=120
                ),
                name="purchase_valid_amount_count",
            )
        ]


class CardInstallment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    purchase = models.ForeignKey(
        CardPurchase, on_delete=models.PROTECT, related_name="installments"
    )
    number = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    closing_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    payment = models.OneToOneField(
        "transactions.FinancialTransaction",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="card_installment",
    )

    class Meta:
        ordering = ["due_date", "purchase_id", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["purchase", "number"], name="single_purchase_installment"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0, number__gte=1), name="installment_positive"
            ),
        ]
        indexes = [models.Index(fields=["household", "due_date"])]


class InstallmentPayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    installment = models.ForeignKey(
        CardInstallment, on_delete=models.PROTECT, related_name="payments"
    )
    transaction = models.OneToOneField(
        "transactions.FinancialTransaction",
        on_delete=models.PROTECT,
        related_name="installment_payment",
    )

    class Meta:
        ordering = ["transaction__effective_date", "id"]
