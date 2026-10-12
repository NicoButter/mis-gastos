from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.credit_cards.views import CardViewSet, InstallmentViewSet, PurchaseViewSet
from apps.recurring.views import OccurrenceViewSet, RecurringViewSet

from .views import AccountViewSet, CategoryViewSet, SummaryView, TransactionViewSet, TransferView

router = DefaultRouter()
router.register("recurring-expenses", RecurringViewSet, basename="recurring-expense")
router.register("recurring-occurrences", OccurrenceViewSet, basename="recurring-occurrence")
router.register("credit-cards", CardViewSet, basename="credit-card")
router.register("card-purchases", PurchaseViewSet, basename="card-purchase")
router.register("card-installments", InstallmentViewSet, basename="card-installment")
router.register("accounts", AccountViewSet, basename="financial-account")
router.register("categories", CategoryViewSet, basename="financial-category")
router.register("transactions", TransactionViewSet, basename="financial-transaction")

urlpatterns = [
    path("", include(router.urls)),
    path("transfers/", TransferView.as_view()),
    path("dashboard/summary/", SummaryView.as_view()),
]
