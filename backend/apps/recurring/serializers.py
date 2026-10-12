from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.transactions.serializers import StrictSerializer

from .models import RecurringExpense, RecurringOccurrence


class RecurringInput(StrictSerializer):
    name = serializers.CharField(max_length=200)
    category_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    frequency = serializers.ChoiceField(choices=["monthly"], default="monthly")
    start_date = serializers.DateField(default=timezone.localdate)
    due_day = serializers.IntegerField(min_value=1, max_value=31)
    account_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class StatusInput(StrictSerializer):
    status = serializers.ChoiceField(choices=["active", "paused", "cancelled"])


class OccurrenceInput(StrictSerializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))


class OccurrencePaymentInput(StrictSerializer):
    account_id = serializers.UUIDField(required=False, allow_null=True)
    effective_date = serializers.DateField(default=timezone.localdate)


class OccurrenceOutput(serializers.ModelSerializer):
    recurring_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(source="recurring.name")
    account_id = serializers.UUIDField(source="recurring.account_id", allow_null=True)
    paid_date = serializers.DateField(source="payment.effective_date", default=None)
    account_name = serializers.CharField(source="payment.account.name", default=None)
    payment_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = RecurringOccurrence
        fields = [
            "id",
            "recurring_id",
            "name",
            "amount",
            "due_date",
            "status",
            "account_id",
            "payment_id",
            "paid_date",
            "account_name",
        ]


class RecurringOutput(serializers.ModelSerializer):
    can_edit = serializers.SerializerMethodField()

    def get_can_edit(self, obj) -> bool:
        membership = self.context.get("membership")
        return bool(
            membership
            and (membership.role in {"owner", "admin"} or membership.user_id == obj.creator_id)
        )

    category_id = serializers.UUIDField(read_only=True)
    account_id = serializers.UUIDField(read_only=True, allow_null=True)
    occurrences = OccurrenceOutput(many=True)

    class Meta:
        model = RecurringExpense
        fields = [
            "id",
            "name",
            "category_id",
            "amount",
            "start_date",
            "due_day",
            "account_id",
            "status",
            "can_edit",
            "occurrences",
        ]
