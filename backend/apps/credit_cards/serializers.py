from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.transactions.serializers import StrictSerializer

from .models import CardInstallment, CardPurchase, CreditCard, InstallmentPayment


class CardInput(StrictSerializer):
    bank = serializers.CharField(max_length=120)
    name = serializers.CharField(max_length=120)
    closing_day = serializers.IntegerField(min_value=1, max_value=31)
    due_day = serializers.IntegerField(min_value=1, max_value=31)
    is_active = serializers.BooleanField(default=True)


class PurchaseInput(StrictSerializer):
    card_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    creditor = serializers.CharField(max_length=200, allow_blank=True, default="")
    first_due_date = serializers.DateField(required=False, allow_null=True)
    frequency = serializers.ChoiceField(choices=["monthly"], default="monthly")
    category_id = serializers.UUIDField()
    description = serializers.CharField(max_length=500)
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    purchase_date = serializers.DateField(default=timezone.localdate)
    installments_count = serializers.IntegerField(min_value=1, max_value=120, default=1)


class PaymentInput(StrictSerializer):
    amount = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal("0.01"), required=False
    )
    account_id = serializers.UUIDField()
    effective_date = serializers.DateField(default=timezone.localdate)


class InstallmentPaymentOutput(serializers.ModelSerializer):
    amount = serializers.DecimalField(source="transaction.amount", max_digits=18, decimal_places=2)
    effective_date = serializers.DateField(source="transaction.effective_date")
    account_name = serializers.CharField(source="transaction.account.name")
    transaction_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = InstallmentPayment
        fields = ["id", "transaction_id", "amount", "effective_date", "account_name"]


class InstallmentOutput(serializers.ModelSerializer):
    paid_amount = serializers.DecimalField(max_digits=24, decimal_places=2, read_only=True)
    pending_amount = serializers.DecimalField(max_digits=24, decimal_places=2, read_only=True)
    payments = InstallmentPaymentOutput(many=True)
    status = serializers.SerializerMethodField()

    def get_status(self, obj) -> str:
        return "paid" if obj.pending_amount == 0 else "partial" if obj.paid_amount else "pending"

    card_name = serializers.CharField(source="purchase.card.name", default=None, allow_null=True)
    description = serializers.CharField(source="purchase.description")
    installments_count = serializers.IntegerField(source="purchase.installments_count")
    payment_id = serializers.UUIDField(read_only=True, allow_null=True)
    paid_date = serializers.DateField(source="payment.effective_date", read_only=True, default=None)
    account_name = serializers.CharField(
        source="payment.account.name", read_only=True, default=None
    )

    class Meta:
        model = CardInstallment
        fields = [
            "id",
            "number",
            "amount",
            "closing_date",
            "due_date",
            "card_name",
            "description",
            "installments_count",
            "payment_id",
            "paid_amount",
            "pending_amount",
            "payments",
            "status",
            "paid_date",
            "account_name",
        ]


class PurchaseOutput(serializers.ModelSerializer):
    card_id = serializers.UUIDField(read_only=True, allow_null=True)
    category_id = serializers.UUIDField(read_only=True)
    installments = InstallmentOutput(many=True)
    pending_amount = serializers.SerializerMethodField()

    def get_pending_amount(self, obj) -> str:
        return str(sum((i.pending_amount for i in obj.installments.all()), Decimal("0.00")))

    class Meta:
        model = CardPurchase
        fields = [
            "id",
            "card_id",
            "category_id",
            "creditor",
            "first_due_date",
            "description",
            "amount",
            "purchase_date",
            "installments_count",
            "pending_amount",
            "installments",
        ]


class CardOutput(serializers.ModelSerializer):
    class Meta:
        model = CreditCard
        fields = ["id", "bank", "name", "closing_day", "due_day", "is_active"]
