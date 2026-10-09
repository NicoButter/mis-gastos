from collections.abc import Mapping
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditEvent
from apps.categories.models import Category
from apps.households.models import Household
from apps.households.services import resolve_active_membership

from . import services
from .serializers import (
    AccountInput,
    AccountOutput,
    AuditOutput,
    CategoryInput,
    CategoryOutput,
    OperationInput,
    OperationOutput,
    SummaryOutput,
    VoidInput,
)

KEY = OpenApiParameter(
    "Idempotency-Key",
    str,
    OpenApiParameter.HEADER,
    required=True,
    description="UUID; scope hogar/usuario; replay 200, contenido diferente 409.",
)
FILTERS = [
    OpenApiParameter(name, str)
    for name in ["from", "to", "type", "account", "category", "status", "search", "ordering"]
]


class FinancialPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class TenantMixin:
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        household_id = request.session.get("active_household_id")
        if not household_id:
            raise ValidationError({"household": "Seleccioná un hogar activo."})
        self.membership = resolve_active_membership(request.user, household_id)
        services.authorize(self.membership)
        expected = request.headers.get("X-Household-ID")
        if expected and expected != str(self.membership.household_id):
            raise services.Conflict("El hogar activo cambió; recargá antes de continuar.")

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "membership": self.membership}

    def mutate(self, request, action_name, input_class, pk=None, partial=False):
        serializer = input_class(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        result, replay = services.write(
            request.user,
            self.membership.household_id,
            request.headers.get("Idempotency-Key"),
            action_name,
            serializer.validated_data,
            pk,
        )
        return Response(
            result, status=status.HTTP_200_OK if replay or pk else status.HTTP_201_CREATED
        )


@extend_schema_view(
    create=extend_schema(request=AccountInput, responses=AccountOutput, parameters=[KEY]),
    partial_update=extend_schema(request=AccountInput, responses=AccountOutput, parameters=[KEY]),
)
class AccountViewSet(TenantMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AccountOutput
    pagination_class = FinancialPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return services.accounts(None)
        return services.accounts(self.membership.household_id).annotate(
            usage_count=Count(
                "entries",
                filter=Q(
                    entries__transaction__creator=self.request.user,
                    entries__transaction__type="expense",
                    entries__transaction__status="posted",
                    entries__revision=F("entries__transaction__revision"),
                ),
            )
        )

    def create(self, request):
        return self.mutate(request, "account.create", AccountInput)

    def partial_update(self, request, pk=None):
        self.get_object()
        return self.mutate(request, "account.update", AccountInput, pk, partial=True)


@extend_schema_view(
    create=extend_schema(request=CategoryInput, responses=CategoryOutput, parameters=[KEY]),
    partial_update=extend_schema(request=CategoryInput, responses=CategoryOutput, parameters=[KEY]),
)
class CategoryViewSet(TenantMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = CategoryOutput
    pagination_class = FinancialPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()
        return Category.objects.filter(household_id=self.membership.household_id).annotate(
            usage_count=Count(
                "financialtransaction",
                filter=Q(
                    financialtransaction__creator=self.request.user,
                    financialtransaction__status="posted",
                ),
            )
        )

    def create(self, request):
        return self.mutate(request, "category.create", CategoryInput)

    def partial_update(self, request, pk=None):
        self.get_object()
        return self.mutate(request, "category.update", CategoryInput, pk, partial=True)


@extend_schema_view(
    list=extend_schema(parameters=FILTERS),
    create=extend_schema(request=OperationInput, responses=OperationOutput, parameters=[KEY]),
    partial_update=extend_schema(
        request=OperationInput, responses=OperationOutput, parameters=[KEY]
    ),
)
class TransactionViewSet(TenantMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = OperationOutput
    pagination_class = FinancialPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return services.operations(None)
        queryset = services.operations(self.membership.household_id)
        params = self.request.query_params
        for key, lookup in [("from", "effective_date__gte"), ("to", "effective_date__lte")]:
            if params.get(key):
                value = serializers.DateField().run_validation(params[key])
                queryset = queryset.filter(**{lookup: value})
        for key in ["type", "status"]:
            if params.get(key):
                allowed = (
                    {"opening", "expense", "income", "transfer"}
                    if key == "type"
                    else {"posted", "voided"}
                )
                if params[key] not in allowed:
                    raise ValidationError({key: "Filtro inválido."})
                queryset = queryset.filter(**{key: params[key]})
        if params.get("account"):
            account_id = serializers.UUIDField().run_validation(params["account"])
            queryset = queryset.filter(Q(account_id=account_id) | Q(destination_id=account_id))
        if params.get("category"):
            queryset = queryset.filter(
                category_id=serializers.UUIDField().run_validation(params["category"])
            )
        if params.get("search"):
            queryset = queryset.filter(description__icontains=params["search"][:200])
        ordering = params.get("ordering", "-effective_date")
        if ordering not in {
            "effective_date",
            "-effective_date",
            "amount",
            "-amount",
            "created_at",
            "-created_at",
        }:
            raise ValidationError({"ordering": "Orden inválido."})
        return queryset.order_by(ordering, "-created_at", "-id")

    def create(self, request):
        return self.mutate(request, "transaction.create", OperationInput)

    def partial_update(self, request, pk=None):
        self.get_object()
        return self.mutate(request, "transaction.update", OperationInput, pk, partial=True)

    @extend_schema(request=VoidInput, responses=OperationOutput, parameters=[KEY])
    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        self.get_object()
        return self.mutate(request, "transaction.void", VoidInput, pk)

    @extend_schema(responses=AuditOutput(many=True))
    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        obj = self.get_object()
        events = AuditEvent.objects.filter(
            household_id=self.membership.household_id, object_id=obj.pk
        ).select_related("actor")
        page = self.paginate_queryset(events)
        result = [
            {
                "action": event.action,
                "actor_name": event.actor.get_full_name() or event.actor.email,
                "before": event.before,
                "after": event.after,
                "created_at": event.created_at,
            }
            for event in page
        ]
        return self.get_paginated_response(AuditOutput(result, many=True).data)


class TransferView(TenantMixin, APIView):
    @extend_schema(request=OperationInput, responses=OperationOutput, parameters=[KEY])
    def post(self, request):
        if not isinstance(request.data, Mapping) or request.data.get("type") != "transfer":
            raise ValidationError({"type": "Este endpoint sólo acepta transferencias."})
        return self.mutate(request, "transaction.create", OperationInput)


class SummaryView(TenantMixin, APIView):
    @extend_schema(
        responses=SummaryOutput,
        parameters=[
            OpenApiParameter(
                "month", str, description="YYYY-MM; mes económico, predeterminado mes local actual"
            )
        ],
    )
    @transaction.atomic
    def get(self, request):
        Household.objects.select_for_update().get(pk=self.membership.household_id)
        services.authorize(resolve_active_membership(request.user, self.membership.household_id))
        raw = request.query_params.get("month", timezone.localdate().strftime("%Y-%m"))
        try:
            start = date.fromisoformat(raw + "-01")
        except ValueError as exc:
            raise ValidationError({"month": "Usá YYYY-MM."}) from exc
        if start.year == 9999 and start.month == 12:
            raise ValidationError({"month": "Período fuera de rango."})
        end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
        current = services.operations(self.membership.household_id).filter(
            status="posted", effective_date__gte=start, effective_date__lt=end
        )
        totals = current.aggregate(
            income=Sum("amount", filter=Q(type="income")),
            expense=Sum("amount", filter=Q(type="expense")),
        )
        income, expense = totals["income"] or Decimal("0"), totals["expense"] or Decimal("0")
        account_list = list(services.accounts(self.membership.household_id))
        distribution = [
            {
                "category_id": str(item["category_id"]),
                "name": item["category__name"],
                "amount": str(item["total"]),
            }
            for item in current.filter(type="expense")
            .values("category_id", "category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        ]
        return Response(
            SummaryOutput(
                {
                    "currency": "ARS",
                    "month": raw,
                    "balance": sum((item.balance for item in account_list), Decimal("0")),
                    "income": income,
                    "expense": expense,
                    "net": income - expense,
                    "count": current.exclude(type="opening").count(),
                    "accounts": account_list,
                    "recent": list(current[:8]),
                    "distribution": distribution,
                },
                context={"membership": self.membership},
            ).data
        )
