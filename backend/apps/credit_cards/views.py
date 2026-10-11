from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.transactions.views import KEY, FinancialPagination, TenantMixin

from . import services
from .models import CreditCard
from .serializers import (
    CardInput,
    CardOutput,
    InstallmentOutput,
    PaymentInput,
    PurchaseInput,
    PurchaseOutput,
)


class CardViewSet(TenantMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CardOutput
    pagination_class = FinancialPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CreditCard.objects.none()
        return CreditCard.objects.filter(household_id=self.membership.household_id)

    @extend_schema(request=CardInput, responses=CardOutput, parameters=[KEY])
    def create(self, request):
        return self.mutate(request, "card.create", CardInput)

    @extend_schema(request=CardInput, responses=CardOutput, parameters=[KEY])
    def partial_update(self, request, pk=None):
        self.get_object()
        return self.mutate(request, "card.update", CardInput, pk, partial=True)


class PurchaseViewSet(TenantMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = PurchaseOutput
    pagination_class = FinancialPagination

    def get_queryset(self):
        return services.purchases(
            None if getattr(self, "swagger_fake_view", False) else self.membership.household_id
        )

    @extend_schema(request=PurchaseInput, responses=PurchaseOutput, parameters=[KEY])
    def create(self, request):
        return self.mutate(request, "card_purchase.create", PurchaseInput)


class InstallmentViewSet(TenantMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = InstallmentOutput
    pagination_class = FinancialPagination

    def get_queryset(self):
        return services.installments(
            None if getattr(self, "swagger_fake_view", False) else self.membership.household_id
        )

    @extend_schema(request=PaymentInput, responses=InstallmentOutput, parameters=[KEY])
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        self.get_object()
        return self.mutate(request, "card_installment.pay", PaymentInput, pk)
