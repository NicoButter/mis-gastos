from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from apps.accounts.views import (
    ActiveHouseholdView,
    AuthConfigurationView,
    CsrfView,
    HouseholdCreateView,
    MeView,
    SessionLogoutView,
)
from apps.households.views import HealthView

urlpatterns = [
    path("api/v1/", include("apps.transactions.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("api/v1/auth/csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("api/v1/auth/config/", AuthConfigurationView.as_view(), name="auth-config"),
    path("api/v1/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/v1/auth/logout/", SessionLogoutView.as_view(), name="auth-logout"),
    path("api/v1/households/", HouseholdCreateView.as_view(), name="household-create"),
    path(
        "api/v1/auth/active-household/",
        ActiveHouseholdView.as_view(),
        name="auth-active-household",
    ),
    path("api/v1/health/", HealthView.as_view(), name="health"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
]
