"""Security regressions through actual HTTP routes and server-side sessions."""

from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.categories.models import Category
from apps.households.models import Household, HouseholdMembership
from apps.transactions.models import WriteReceipt
from tests.test_commitments import recurring
from tests.test_credit_cards import card, purchase
from tests.test_finance import account, payload, post
from tests.test_finance import context as finance_context

context = finance_context
pytestmark = pytest.mark.django_db(transaction=True)

RESOURCES = (
    "accounts",
    "categories",
    "transactions",
    "credit-cards",
    "card-purchases",
    "card-installments",
    "recurring-expenses",
    "recurring-occurrences",
)


@pytest.fixture
def private_routes(context):
    client, _, home, _ = context
    source = account(client)
    operation = post(client, "transactions", payload(home, source)).data
    card_id = card(client)
    bought = purchase(client, home, card_id)
    assert bought.status_code == 201, bought.data
    rule = recurring(client, home, source)
    assert rule.status_code == 201, rule.data
    ids = {
        "accounts": source,
        "categories": str(Category.objects.filter(household=home).first().pk),
        "transactions": operation["id"],
        "credit-cards": card_id,
        "card-purchases": bought.data["id"],
        "card-installments": bought.data["installments"][0]["id"],
        "recurring-expenses": rule.data["id"],
        "recurring-occurrences": rule.data["occurrences"][0]["id"],
    }
    routes = [("get", f"{resource}/{pk}") for resource, pk in ids.items()]
    routes += [
        ("patch", f"{resource}/{ids[resource]}")
        for resource in (
            "accounts",
            "categories",
            "transactions",
            "credit-cards",
            "recurring-expenses",
            "recurring-occurrences",
        )
    ]
    routes += [
        ("get", f"transactions/{operation['id']}/history"),
        ("post", f"transactions/{operation['id']}/void"),
        ("post", f"card-installments/{ids['card-installments']}/pay"),
        ("post", f"recurring-occurrences/{ids['recurring-occurrences']}/pay"),
    ]
    return routes, ids


def request_route(client, method, path):
    url = f"/api/v1/{path}/" if path else "/api/v1/"
    if method == "get":
        return client.get(url)
    return getattr(client, method)(url, {}, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4()))


def test_every_financial_route_requires_authentication(private_routes):
    routes, _ = private_routes
    routes += [("get", resource) for resource in RESOURCES]
    routes += [
        ("post", resource)
        for resource in (
            "accounts",
            "categories",
            "transactions",
            "credit-cards",
            "card-purchases",
            "recurring-expenses",
            "transfers",
            "households",
            "auth/active-household",
            "auth/logout",
        )
    ]
    routes += [("get", "dashboard/summary"), ("get", "auth/me"), ("get", "")]
    for method, path in routes:
        response = request_route(APIClient(), method, path)
        assert response.status_code in {401, 403}, (method, path, response.data)


@pytest.mark.parametrize("attack", ["own_tenant", "forged_session", "revoked", "multi_tenant"])
def test_other_users_objects_and_actions_are_inaccessible(context, private_routes, attack):
    _, _, home, _ = context
    routes, ids = private_routes
    attacker = User.objects.create_user("attacker@example.com", "password")
    own = Household.objects.create(name="Attacker's household")
    HouseholdMembership.objects.create(user=attacker, household=own, role="owner")
    if attack in {"revoked", "multi_tenant"}:
        HouseholdMembership.objects.create(
            user=attacker,
            household=home,
            role="owner",
            status="revoked" if attack == "revoked" else "active",
        )
    client = APIClient()
    client.force_login(attacker)
    session = client.session
    session["active_household_id"] = str(
        home.pk if attack in {"forged_session", "revoked"} else own.pk
    )
    session.save()
    before = WriteReceipt.objects.count()
    for method, path in routes:
        response = request_route(client, method, path)
        assert response.status_code == 404, (attack, method, path, response.data)
        assert not any(pk in response.content.decode() for pk in ids.values())
    for resource in RESOURCES:
        response = client.get(f"/api/v1/{resource}/")
        if attack in {"forged_session", "revoked"}:
            assert response.status_code == 404
        else:
            assert response.status_code == 200, response.data
            assert response.data["count"] == 0
    summary = client.get("/api/v1/dashboard/summary/")
    if attack in {"forged_session", "revoked"}:
        assert summary.status_code == 404
    else:
        assert summary.data["balance"] == "0.00"
        assert summary.data["recent"] == []
    assert WriteReceipt.objects.count() == before


def test_all_mutating_routes_enforce_session_csrf(context, private_routes):
    _, user, home, _ = context
    routes, _ = private_routes
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    session = client.session
    session["active_household_id"] = str(home.pk)
    session.save()
    routes += [
        ("post", resource)
        for resource in (
            "accounts",
            "categories",
            "transactions",
            "credit-cards",
            "card-purchases",
            "recurring-expenses",
            "transfers",
            "households",
            "auth/active-household",
            "auth/logout",
        )
    ]
    for method, path in routes:
        if method != "get":
            response = request_route(client, method, path)
            assert response.status_code == 403, (method, path, response.data)


def test_private_responses_cannot_be_cached_across_sessions(context):
    client, _, _, _ = context
    for path in ["auth/me", "accounts", "dashboard/summary"]:
        response = client.get(f"/api/v1/{path}/")
        assert response.status_code == 200
        assert "no-store" in response["Cache-Control"]
        assert "private" in response["Cache-Control"]
        assert "Cookie" in response["Vary"]
    response = APIClient().get("/api/v1/auth/me/")
    assert "no-store" in response["Cache-Control"]


def test_global_admin_denies_tenant_staff_even_with_model_permissions():
    staff = User.objects.create_user("staff@example.com", "password", is_staff=True)
    staff.user_permissions.set(Permission.objects.filter(content_type__app_label="households"))
    client = APIClient()
    client.force_login(staff)
    for path in ["/admin/", "/admin/households/household/", "/admin/accounts/user/"]:
        response = client.get(path)
        assert response.status_code == 302
        assert response["Location"].startswith("/admin/login/")
    operator = User.objects.create_superuser("operator@example.com", "password")
    client.force_login(operator)
    assert client.get("/admin/households/household/").status_code == 200


def test_deactivated_user_cannot_resolve_tenant_membership(context):
    from rest_framework.exceptions import NotAuthenticated

    from apps.households.services import resolve_active_membership

    _, user, home, _ = context
    user.is_active = False
    user.save(update_fields=["is_active"])
    with pytest.raises(NotAuthenticated):
        resolve_active_membership(user, home.pk)


def test_idempotency_receipts_are_isolated_by_user(context):
    client, _, home, _ = context
    source = account(client)
    data, key = payload(home, source), uuid4()
    first = post(client, "transactions", data, key)
    assert first.status_code == 201
    member = User.objects.create_user("second-member@example.com", "password")
    HouseholdMembership.objects.create(user=member, household=home, role="member")
    client.force_login(member)
    session = client.session
    session["active_household_id"] = str(home.pk)
    session.save()
    second = post(client, "transactions", data, key)
    assert second.status_code == 201, second.data
    assert second.data["id"] != first.data["id"]
    assert WriteReceipt.objects.filter(household=home, key=key).count() == 2


def test_idempotency_receipts_are_isolated_by_household(context):
    client, user, home, _ = context
    data = {"name": "Efectivo", "kind": "cash", "opening_balance": "0.00"}
    key = uuid4()
    first = post(client, "accounts", data, key)
    assert first.status_code == 201
    second_home = Household.objects.create(name="Second household")
    HouseholdMembership.objects.create(user=user, household=second_home, role="owner")
    selected = client.post(
        "/api/v1/auth/active-household/", {"householdId": str(second_home.pk)}, format="json"
    )
    assert selected.status_code == 200
    second = post(client, "accounts", data, key)
    assert second.status_code == 201, second.data
    assert second.data["id"] != first.data["id"]
    assert WriteReceipt.objects.filter(actor=user, key=key).count() == 2
    assert client.get(f"/api/v1/accounts/{first.data['id']}/").status_code == 404
    assert client.get("/api/v1/accounts/", HTTP_X_HOUSEHOLD_ID=str(home.pk)).status_code == 409
