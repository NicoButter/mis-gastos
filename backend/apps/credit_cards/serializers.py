from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.transactions.serializers import StrictSerializer

from .models import CardInstallment, CardPurchase, CreditCard


class CardInput(StrictSerializer):
    bank = serializers.CharField(max_length=120)
    name = serializers.CharField(max_length=120)
    closing_day = serializers.IntegerField(min_value=1, max_value=31)
    due_day = serializers.IntegerField(min_value=1, max_value=31)
    is_active = serializers.BooleanField(default=True)


class PurchaseInput(StrictSerializer):
    card_id = serializers.UUIDField()
    category_id = serializers.UUIDField()
    description = serializers.CharField(max_length=500)
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    purchase_date = serializers.DateField(default=timezone.localdate)
    installments_count = serializers.IntegerField(min_value=1, max_value=120, default=1)


class PaymentInput(StrictSerializer):
    account_id = serializers.UUIDField()
    effective_date = serializers.DateField(default=timezone.localdate)


class InstallmentOutput(serializers.ModelSerializer):
    card_name = serializers.CharField(source="purchase.card.name")
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
            "paid_date",
            "account_name",
        ]


class PurchaseOutput(serializers.ModelSerializer):
    card_id = serializers.UUIDField(read_only=True)
    category_id = serializers.UUIDField(read_only=True)
    installments = InstallmentOutput(many=True)
    pending_amount = serializers.SerializerMethodField()

    def get_pending_amount(self, obj) -> str:
        return str(
            sum((i.amount for i in obj.installments.all() if not i.payment_id), Decimal("0.00"))
        )

    class Meta:
        model = CardPurchase
        fields = [
            "id",
            "card_id",
            "category_id",
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
