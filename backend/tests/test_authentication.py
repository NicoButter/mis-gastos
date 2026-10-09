from unittest.mock import Mock

import pytest
from allauth.account import app_settings as allauth_account_settings
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.adapters import GastioSocialAccountAdapter
from apps.accounts.models import User
from apps.households.models import Household, HouseholdMembership


def test_allauth_is_configured_for_the_username_free_user_model():
    assert allauth_account_settings.USER_MODEL_USERNAME_FIELD is None


def test_csrf_endpoint_sets_a_cookie_without_exposing_secrets():
    response = APIClient(enforce_csrf_checks=True).get("/api/v1/auth/csrf/")
    assert response.status_code == 200
    assert response.json()["csrfToken"]
    assert "csrftoken" in response.cookies


@pytest.mark.django_db
def test_me_requires_a_django_session():
    response = APIClient().get("/api/v1/auth/me/")
    assert response.status_code in {401, 403}
    assert "password" not in response.content.decode().lower()


@pytest.mark.django_db
def test_me_returns_only_active_memberships_and_server_validated_active_household():
    user = User.objects.create_user("member@example.com", "password")
    active = Household.objects.create(name="Hogar activo")
    revoked = Household.objects.create(name="Hogar revocado")
    HouseholdMembership.objects.create(user=user, household=active)
    HouseholdMembership.objects.create(
        user=user, household=revoked, status=HouseholdMembership.Status.REVOKED
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/v1/auth/me/")

    assert response.status_code == 200
    assert response.json()["user"]["id"] == str(user.id)
    assert response.json()["households"] == [
        {"id": str(active.id), "name": "Hogar activo", "role": "member"}
    ]


@pytest.mark.django_db
def test_active_household_rejects_another_users_tenant():
    user = User.objects.create_user("member@example.com", "password")
    other_home = Household.objects.create(name="Hogar ajeno")
    client = APIClient()
    client.force_authenticate(user)

    response = client.post("/api/v1/auth/active-household/", {"householdId": str(other_home.id)})

    assert response.status_code == 404


@pytest.mark.django_db
def test_onboarding_explicitly_creates_the_first_household_and_owner_membership():
    user = User.objects.create_user("new@example.com", "password")
    client = APIClient()
    client.force_authenticate(user)

    response = client.post("/api/v1/households/", {"name": "Mi hogar"})

    assert response.status_code == 201
    membership = HouseholdMembership.objects.get(user=user)
    assert membership.household.name == "Mi hogar"
    assert membership.role == HouseholdMembership.Role.OWNER
    assert response.json()["activeHousehold"]["id"] == str(membership.household_id)


@pytest.mark.django_db
def test_logout_invalidates_the_django_session_with_csrf_protection():
    user = User.objects.create_user("member@example.com", "password")
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    csrf = client.get("/api/v1/auth/csrf/").json()["csrfToken"]

    rejected = client.post("/api/v1/auth/logout/", {})
    response = client.post("/api/v1/auth/logout/", {}, HTTP_X_CSRFTOKEN=csrf)

    assert rejected.status_code == 403
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me/").status_code in {401, 403}


@pytest.mark.django_db
def test_existing_google_identity_is_reused_without_creating_another_user():
    user = User.objects.create_user("person@example.com", "password")
    account = SocialAccount.objects.create(user=user, provider="google", uid="google-subject-1")

    assert SocialAccount.objects.get(provider="google", uid="google-subject-1").user_id == user.id
    assert User.objects.filter(email="person@example.com").count() == 1
    assert account.uid == "google-subject-1"


@pytest.mark.django_db
def test_unlinked_google_email_cannot_silently_take_over_an_existing_user():
    existing = User.objects.create_user("person@example.com", "password")
    social_login = SocialLogin(
        account=SocialAccount(provider="google", uid="new-google-subject"),
        user=User(email=existing.email),
    )

    with pytest.raises(ImmediateHttpResponse) as raised:
        GastioSocialAccountAdapter().pre_social_login(Mock(), social_login)

    assert "account_link_required" in raised.value.response["Location"]
    assert User.objects.filter(email=existing.email).count() == 1


@override_settings(GOOGLE_OAUTH_CONFIGURED=False)
def test_auth_configuration_reports_missing_google_credentials_safely():
    response = APIClient().get("/api/v1/auth/config/")
    assert response.status_code == 200
    assert response.json() == {"googleLoginEnabled": False}
