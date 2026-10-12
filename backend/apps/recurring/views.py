from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.transactions.views import KEY, FinancialPagination, TenantMixin

from . import services
from .serializers import (
    OccurrenceInput,
    OccurrenceOutput,
    OccurrencePaymentInput,
    RecurringInput,
    RecurringOutput,
    StatusInput,
)


class RecurringViewSet(TenantMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = RecurringOutput
    pagination_class = FinancialPagination

    def get_queryset(self):
        return services.rules(
            None if getattr(self, "swagger_fake_view", False) else self.membership.household_id
        )

    def list(self, request, *args, **kwargs):
        services.ensure_occurrences(request.user, self.membership.household_id)
        return super().list(request, *args, **kwargs)

    @extend_schema(request=RecurringInput, responses=RecurringOutput, parameters=[KEY])
    def create(self, request):
        return self.mutate(request, "recurring.create", RecurringInput)

    @extend_schema(request=StatusInput, responses=RecurringOutput, parameters=[KEY])
    def partial_update(self, request, pk=None):
        self.get_object()
        return self.mutate(request, "recurring.update", StatusInput, pk)


class OccurrenceViewSet(TenantMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = OccurrenceOutput
    pagination_class = FinancialPagination

    def get_queryset(self):
        return services.occurrences(
            None if getattr(self, "swagger_fake_view", False) else self.membership.household_id
        )

    def list(self, request, *args, **kwargs):
        services.ensure_occurrences(request.user, self.membership.household_id)
        return super().list(request, *args, **kwargs)

    @extend_schema(request=OccurrenceInput, responses=OccurrenceOutput, parameters=[KEY])
    def partial_update(self, request, pk=None):
        self.get_object()
        return self.mutate(request, "recurring_occurrence.update", OccurrenceInput, pk)

    @extend_schema(request=OccurrencePaymentInput, responses=OccurrenceOutput, parameters=[KEY])
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        self.get_object()
        return self.mutate(request, "recurring_occurrence.pay", OccurrencePaymentInput, pk)
