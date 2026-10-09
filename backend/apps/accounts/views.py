from __future__ import annotations

from urllib.parse import urlparse

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.categories.services import seed_categories
from apps.households.models import Household, HouseholdMembership
from apps.households.services import resolve_active_membership

from .serializers import (
    AuthConfigurationOutput,
    CsrfOutput,
    HouseholdInput,
    HouseholdSelectionInput,
    SelectionOutput,
    SessionOutput,
)


def serialize_membership(membership: HouseholdMembership) -> dict[str, str]:
    return {
        "id": str(membership.household_id),
        "name": membership.household.name,
        "role": membership.role,
    }


def google_avatar_url(extra_data: dict[str, object] | None) -> str | None:
    """Return only the HTTPS avatar URL received from Google's callback."""
    picture = extra_data.get("picture") if extra_data else None
    if not isinstance(picture, str):
        return None
    parsed = urlparse(picture)
    hostname = parsed.hostname
    if (
        parsed.scheme != "https"
        or not hostname
        or not (hostname == "googleusercontent.com" or hostname.endswith(".googleusercontent.com"))
    ):
        return None
    return picture


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """Sets Django's CSRF cookie before the browser posts to Allauth."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=CsrfOutput)
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class MeView(APIView):
    """Session-backed identity and memberships; no OAuth tokens are exposed."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SessionOutput)
    def get(self, request):
        google_account_data = (
            SocialAccount.objects.filter(user=request.user, provider="google")
            .values_list("extra_data", flat=True)
            .first()
        )
        memberships = list(
            HouseholdMembership.objects.select_related("household")
            .filter(user=request.user, status=HouseholdMembership.Status.ACTIVE)
            .order_by("household__name", "household_id")
        )
        active_household = None
        active_id = request.session.get("active_household_id")
        if active_id:
            active_household = next(
                (item for item in memberships if str(item.household_id) == str(active_id)), None
            )
            if active_household is None:
                request.session.pop("active_household_id", None)
        if active_household is None and len(memberships) == 1:
            active_household = memberships[0]
            request.session["active_household_id"] = str(active_household.household_id)
        return Response(
            {
                "user": {
                    "id": str(request.user.id),
                    "email": request.user.email,
                    "displayName": request.user.get_full_name() or request.user.email,
                    "avatarUrl": google_avatar_url(google_account_data),
                },
                "households": [serialize_membership(item) for item in memberships],
                "activeHousehold": (
                    serialize_membership(active_household) if active_household else None
                ),
            }
        )


class ActiveHouseholdView(APIView):
    """Persists only a server-validated active tenant in the Django session."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=HouseholdSelectionInput, responses=SelectionOutput)
    def post(self, request):
        household_id = request.data.get("householdId")
        membership = resolve_active_membership(request.user, household_id)
        request.session["active_household_id"] = str(membership.household_id)
        return Response({"activeHousehold": serialize_membership(membership)})


class HouseholdCreateView(APIView):
    """The minimal onboarding write: create a user's first household explicitly."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=HouseholdInput, responses={201: SelectionOutput})
    def post(self, request):
        name = request.data.get("name", "")
        if not isinstance(name, str) or not (name := name.strip()):
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "Nombre de hogar requerido."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(name) > 120:
            return Response(
                {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Nombre de hogar demasiado largo.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            household = Household.objects.create(name=name)
            membership = HouseholdMembership.objects.create(
                user=request.user,
                household=household,
                role=HouseholdMembership.Role.OWNER,
            )
            seed_categories(household.id)
            request.session["active_household_id"] = str(household.id)
        return Response(
            {"activeHousehold": serialize_membership(membership)}, status=status.HTTP_201_CREATED
        )


class SessionLogoutView(APIView):
    """POST-only logout; SessionAuthentication enforces Django CSRF checks."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        from django.contrib.auth import logout

        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthConfigurationView(APIView):
    """Public, non-sensitive capability signal for the login UI."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=AuthConfigurationOutput)
    def get(self, request):
        return Response({"googleLoginEnabled": settings.GOOGLE_OAUTH_CONFIGURED})
