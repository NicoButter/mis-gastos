from collections.abc import Mapping
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.categories.models import Category
from apps.wallets.models import FinancialAccount

from .models import FinancialTransaction


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            raise serializers.ValidationError({"non_field_errors": ["Se requiere un objeto JSON."]})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: ["Campo no permitido."] for key in unknown})
        return super().to_internal_value(data)


class AccountInput(StrictSerializer):
    name = serializers.CharField(max_length=120)
    kind = serializers.ChoiceField(choices=FinancialAccount.Kind.choices)
    currency = serializers.ChoiceField(choices=["ARS"], default="ARS")
    description = serializers.CharField(max_length=500, allow_blank=True, default="")
    opening_balance = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal("0"), default=Decimal("0")
    )
    opening_date = serializers.DateField(default=timezone.localdate)
    is_active = serializers.BooleanField(default=True)


class CategoryInput(StrictSerializer):
    name = serializers.CharField(max_length=100)
    type = serializers.ChoiceField(choices=["income", "expense"])
    slug = serializers.SlugField(max_length=120, required=False)
    is_active = serializers.BooleanField(default=True)
    color = serializers.RegexField(r"^#[0-9a-fA-F]{6}$", allow_blank=True, default="")


class OperationInput(StrictSerializer):
    type = serializers.ChoiceField(choices=["income", "expense", "transfer"])
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    account_id = serializers.UUIDField()
    destination_id = serializers.UUIDField(required=False, allow_null=True)
    category_id = serializers.UUIDField(required=False, allow_null=True)
    effective_date = serializers.DateField(default=timezone.localdate)
    description = serializers.CharField(max_length=500, allow_blank=True, default="")
    expected_revision = serializers.IntegerField(min_value=1, required=False)


class VoidInput(StrictSerializer):
    expected_revision = serializers.IntegerField(min_value=1)


class AccountOutput(serializers.ModelSerializer):
    usage_count = serializers.IntegerField(read_only=True, default=0)
    balance = serializers.DecimalField(max_digits=24, decimal_places=2, read_only=True)

    class Meta:
        model = FinancialAccount
        fields = [
            "id",
            "name",
            "kind",
            "currency",
            "description",
            "is_active",
            "balance",
            "usage_count",
            "created_at",
            "updated_at",
        ]


class CategoryOutput(serializers.ModelSerializer):
    usage_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = ["id", "name", "type", "slug", "is_active", "color", "usage_count"]


class OperationOutput(serializers.ModelSerializer):
    account_id = serializers.UUIDField(read_only=True)
    destination_id = serializers.UUIDField(read_only=True, allow_null=True)
    category_id = serializers.UUIDField(read_only=True, allow_null=True)
    account_name = serializers.CharField(source="account.name", read_only=True)
    destination_name = serializers.CharField(
        source="destination.name", read_only=True, default=None
    )
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    creator_name = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    def get_creator_name(self, obj) -> str:
        return obj.creator.get_full_name() or obj.creator.email

    def get_can_edit(self, obj) -> bool:
        membership = self.context.get("membership")
        return bool(
            membership
            and obj.type != "opening"
            and obj.status == "posted"
            and (membership.role in {"owner", "admin"} or membership.user_id == obj.creator_id)
        )

    class Meta:
        model = FinancialTransaction
        fields = [
            "id",
            "type",
            "amount",
            "currency",
            "effective_date",
            "description",
            "account_id",
            "destination_id",
            "category_id",
            "account_name",
            "destination_name",
            "category_name",
            "creator_name",
            "status",
            "revision",
            "can_edit",
            "created_at",
            "updated_at",
        ]


class AuditOutput(serializers.Serializer):
    action = serializers.CharField()
    actor_name = serializers.CharField()
    before = serializers.JSONField()
    after = serializers.JSONField()
    created_at = serializers.DateTimeField()


class SummaryOutput(serializers.Serializer):
    currency = serializers.CharField()
    month = serializers.CharField()
    balance = serializers.DecimalField(max_digits=24, decimal_places=2)
    income = serializers.DecimalField(max_digits=24, decimal_places=2)
    expense = serializers.DecimalField(max_digits=24, decimal_places=2)
    net = serializers.DecimalField(max_digits=24, decimal_places=2)
    count = serializers.IntegerField()
    accounts = AccountOutput(many=True)
    recent = OperationOutput(many=True)
    distribution = serializers.ListField(child=serializers.DictField())
