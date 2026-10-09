from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, CategoryViewSet, SummaryView, TransactionViewSet, TransferView

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="financial-account")
router.register("categories", CategoryViewSet, basename="financial-category")
router.register("transactions", TransactionViewSet, basename="financial-transaction")

urlpatterns = [
    path("", include(router.urls)),
    path("transfers/", TransferView.as_view()),
    path("dashboard/summary/", SummaryView.as_view()),
]
