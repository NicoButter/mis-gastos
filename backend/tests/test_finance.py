from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import IntegrityError, close_old_connections, connection, connections, transaction
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.categories.models import Category
from apps.categories.services import seed_categories
from apps.households.models import Household, HouseholdMembership
from apps.transactions.models import FinancialTransaction, LedgerEntry
from apps.transactions.serializers import OperationInput
from apps.transactions.services import accounts, write
from apps.wallets.models import FinancialAccount

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def context():
    user = User.objects.create_user("finance@example.com", "password")
    home = Household.objects.create(name="Finanzas")
    membership = HouseholdMembership.objects.create(user=user, household=home, role="owner")
    seed_categories(home.id)
    client = APIClient()
    client.force_login(user)
    session = client.session
    session["active_household_id"] = str(home.id)
    session.save()
    return client, user, home, membership


def post(client, path, data, key=None):
    return client.post(
        f"/api/v1/{path}/", data, format="json", HTTP_IDEMPOTENCY_KEY=str(key or uuid4())
    )


def account(client, name="Efectivo", opening="100.00"):
    result = post(
        client,
        "accounts",
        {"name": name, "kind": "cash", "opening_balance": opening, "opening_date": "2026-09-01"},
    )
    assert result.status_code == 201, result.data
    return result.data["id"]


def payload(home, source, kind="expense", amount="10.25", **extra):
    data = {
        "type": kind,
        "amount": amount,
        "account_id": source,
        "effective_date": "2026-10-01",
        "description": "Operación",
    }
    if kind != "transfer":
        data["category_id"] = str(Category.objects.filter(household=home, type=kind).first().id)
    return {**data, **extra}


def test_full_financial_lifecycle_and_monthly_dashboard(context):
    client, _, home, _ = context
    source = account(client)
    target = account(client, "Banco", "0")
    expense = post(client, "transactions", payload(home, source)).data
    assert post(client, "transactions", payload(home, source, "income", "20.50")).status_code == 201
    transfer = post(
        client, "transfers", payload(home, source, "transfer", "50.00", destination_id=target)
    )
    assert transfer.status_code == 201
    assert LedgerEntry.objects.filter(transaction_id=transfer.data["id"]).count() == 2
    balances = {str(a.id): a.balance for a in accounts(home.id)}
    assert balances == {source: Decimal("60.25"), target: Decimal("50.00")}
    summary = client.get("/api/v1/dashboard/summary/?month=2026-10").data
    assert (
        summary["balance"],
        summary["income"],
        summary["expense"],
        summary["net"],
        summary["count"],
    ) == ("110.25", "20.50", "10.25", "10.25", 3)
    assert summary["distribution"][0]["amount"] == "10.25"
    account_response = client.get(f"/api/v1/accounts/{source}/").data
    assert account_response["usage_count"] == 1 and account_response["balance"] == "60.25"
    assert client.get("/api/v1/dashboard/summary/?month=2026-09").data["income"] == "0.00"
    response = client.patch(
        f'/api/v1/transactions/{expense["id"]}/',
        {"amount": "15.00", "expected_revision": 1},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert response.status_code == 200, response.data
    assert response.data["revision"] == 2
    assert LedgerEntry.objects.filter(transaction_id=expense["id"]).count() == 2
    voided = post(client, f'transactions/{expense["id"]}/void', {"expected_revision": 2})
    assert voided.status_code == 200
    assert client.get(f"/api/v1/accounts/{source}/").data["usage_count"] == 0
    assert client.get("/api/v1/dashboard/summary/?month=2026-10").data["expense"] == "0.00"
    assert AuditEvent.objects.filter(object_id=expense["id"]).count() == 3
    assert client.get(f'/api/v1/transactions/{expense["id"]}/history/').data["count"] == 3


@pytest.mark.parametrize("amount", ["0", "-1", "1.001", "NaN", "Infinity", "10000000000000000"])
def test_invalid_amounts_do_not_write(context, amount):
    client, _, home, _ = context
    source = account(client, opening="0")
    assert post(client, "transactions", payload(home, source, amount=amount)).status_code == 400
    assert not FinancialTransaction.objects.exists()


def test_negative_balance_and_backdated_expense_are_supported(context):
    client, _, home, _ = context
    source = account(client, opening="0")
    assert (
        post(
            client,
            "transactions",
            payload(home, source, amount="0.10", effective_date="2020-02-29"),
        ).status_code
        == 201
    )
    assert accounts(home.id).get(pk=source).balance == Decimal("-0.10")
    assert (
        post(client, "transactions", payload(home, source, effective_date="2026-02-30")).status_code
        == 400
    )


def test_idempotency_conflict_and_stale_correction(context):
    client, _, home, _ = context
    source = account(client, opening="0")
    data, key = payload(home, source), uuid4()
    first = post(client, "transactions", data, key)
    replay = post(client, "transactions", data, key)
    assert replay.status_code == 200 and replay.data["id"] == first.data["id"]
    assert post(client, "transactions", {**data, "amount": "12"}, key).status_code == 409
    assert FinancialTransaction.objects.count() == 1
    url = f'/api/v1/transactions/{first.data["id"]}/'
    assert (
        client.patch(
            url,
            {"amount": "20", "expected_revision": 1},
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        ).status_code
        == 200
    )
    assert (
        client.patch(
            url,
            {"amount": "30", "expected_revision": 1},
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        ).status_code
        == 409
    )
    assert client.post("/api/v1/transactions/", data, format="json").status_code == 400


def test_archive_preserves_balance_blocks_new_operations_and_no_delete(context):
    client, _, home, _ = context
    source = account(client)
    response = client.patch(
        f"/api/v1/accounts/{source}/",
        {"is_active": False},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert response.status_code == 200 and response.data["balance"] == "100.00"
    assert post(client, "transactions", payload(home, source)).status_code == 400
    assert client.delete(f"/api/v1/accounts/{source}/").status_code == 405
    assert client.get("/api/v1/dashboard/summary/").data["balance"] == "100.00"


def test_categories_are_idempotent_tenant_scoped_and_stable(context):
    client, _, home, _ = context
    seed_categories(home.id)
    assert Category.objects.filter(household=home).count() == 18
    response = post(client, "categories", {"name": "Club", "type": "expense"})
    assert response.status_code == 201
    url = f'/api/v1/categories/{response.data["id"]}/'
    assert (
        client.patch(
            url, {"type": "income"}, format="json", HTTP_IDEMPOTENCY_KEY=str(uuid4())
        ).status_code
        == 400
    )
    assert (
        client.patch(
            url,
            {"name": "Club familiar", "is_active": False},
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        ).status_code
        == 200
    )
    assert client.delete(url).status_code == 405


def test_cross_tenant_queries_bodies_filters_and_revocation(context):
    client, user, home, membership = context
    own = account(client)
    other = Household.objects.create(name="Otro")
    foreign = FinancialAccount.objects.create(household=other, name="Privada", kind="bank")
    seed_categories(other.id)
    HouseholdMembership.objects.create(user=user, household=other)
    assert post(client, "transactions", payload(home, foreign.id)).status_code == 404
    assert (
        post(
            client,
            "transactions",
            payload(
                home, own, category_id=str(Category.objects.filter(household=other).first().id)
            ),
        ).status_code
        == 404
    )
    assert client.get(f"/api/v1/accounts/{foreign.id}/").status_code == 404
    assert client.get(f"/api/v1/transactions/?account={foreign.id}").data["count"] == 0
    assert (
        post(
            client, "accounts", {"name": "Attack", "kind": "cash", "household_id": str(other.id)}
        ).status_code
        == 400
    )
    membership.status = "revoked"
    membership.save()
    assert client.get("/api/v1/accounts/").status_code == 404


def test_permissions_member_own_only_limited_denied_and_anonymous(context):
    client, _, home, _ = context
    source = account(client)
    operation = post(client, "transactions", payload(home, source)).data
    member = User.objects.create_user("member-finance@example.com")
    membership = HouseholdMembership.objects.create(user=member, household=home)
    client.force_login(member)
    session = client.session
    session["active_household_id"] = str(home.id)
    session.save()
    assert post(client, "accounts", {"name": "Denied", "kind": "cash"}).status_code == 403
    assert (
        post(client, f'transactions/{operation["id"]}/void', {"expected_revision": 1}).status_code
        == 403
    )
    own = post(client, "transactions", payload(home, source)).data
    assert (
        post(client, f'transactions/{own["id"]}/void', {"expected_revision": 1}).status_code == 200
    )
    membership.role = "limited_entry"
    membership.save()
    assert client.get("/api/v1/dashboard/summary/").status_code == 403
    assert client.get("/api/v1/accounts/").status_code == 403
    client.logout()
    assert client.get("/api/v1/accounts/").status_code == 403


def test_filters_pagination_and_empty_dashboard(context):
    client, _, home, _ = context
    empty = client.get("/api/v1/dashboard/summary/?month=2026-10").data
    assert empty["balance"] == empty["income"] == empty["expense"] == "0.00"
    source = account(client, opening="0")
    for i in range(3):
        post(
            client,
            "transactions",
            payload(home, source, amount=str(i + 1), description=f"Filtro {i}"),
        )
    result = client.get(
        "/api/v1/transactions/?page_size=2&type=expense&from=2026-10-01&to=2026-10-01&ordering=amount"
    ).data
    assert result["count"] == 3 and len(result["results"]) == 2 and result["next"]
    assert client.get("/api/v1/transactions/?search=Filtro%202").data["count"] == 1
    assert client.get("/api/v1/transactions/?account=invalid").status_code == 400


def test_transfer_correction_void_and_atomic_rollback(context):
    client, _, home, _ = context
    source, destination = account(client), account(client, "Destino", "0")
    assert (
        post(
            client, "transfers", payload(home, source, "transfer", destination_id=source)
        ).status_code
        == 400
    )
    data = payload(home, source, "transfer", destination_id=destination)
    with patch(
        "apps.transactions.services.LedgerEntry.objects.bulk_create",
        side_effect=RuntimeError("Injected failure"),
    ):
        with pytest.raises(RuntimeError):
            post(client, "transfers", data)
    assert FinancialTransaction.objects.filter(type="transfer").count() == 0
    op = post(client, "transfers", data).data
    url = f'/api/v1/transactions/{op["id"]}/'
    assert (
        client.patch(
            url,
            {"amount": "25.00", "expected_revision": 1},
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        ).status_code
        == 200
    )
    assert sum(a.balance for a in accounts(home.id)) == Decimal("100")
    assert (
        post(client, f'transactions/{op["id"]}/void', {"expected_revision": 2}).status_code == 200
    )
    assert accounts(home.id).get(pk=source).balance == Decimal("100")


def test_postgresql_rejects_partial_and_mutable_ledger(context):
    client, user, home, _ = context
    source = account(client)
    with pytest.raises(IntegrityError), transaction.atomic():
        FinancialTransaction.objects.create(
            household=home,
            creator=user,
            type="opening",
            amount="1",
            account_id=source,
            effective_date=date(2026, 10, 1),
        )
    entry = LedgerEntry.objects.first()
    with pytest.raises(IntegrityError), transaction.atomic():
        LedgerEntry.objects.filter(pk=entry.pk).update(amount=Decimal("999"))
    with pytest.raises(IntegrityError), transaction.atomic():
        AuditEvent.objects.all().delete()


def test_concurrent_identical_writes_post_once(context):
    client, user, home, _ = context
    source = account(client, opening="0")
    serializer = OperationInput(data=payload(home, source))
    serializer.is_valid(raise_exception=True)
    key = uuid4()

    def run():
        close_old_connections()
        try:
            return write(
                User.objects.get(pk=user.pk),
                home.id,
                key,
                "transaction.create",
                serializer.validated_data,
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: run(), range(2)))
    assert sorted(replay for _, replay in results) == [False, True]
    assert results[0][0]["id"] == results[1][0]["id"]
    assert FinancialTransaction.objects.count() == 1
    assert accounts(home.id).get(pk=source).balance == Decimal("-10.25")


def test_postgresql_schema_guards_installed():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM pg_trigger WHERE tgname IN "
            "('operation_consistent', 'ledger_consistent', 'ledger_immutable')"
        )
        assert cursor.fetchone()[0] == 3


def test_csrf_context_mismatch_and_invalid_json_are_rejected(context):
    client, user, home, _ = context
    source = account(client, opening="0")
    assert client.get("/api/v1/accounts/", HTTP_X_HOUSEHOLD_ID=str(uuid4())).status_code == 409
    assert post(client, "transactions", ["invalid"]).status_code == 400
    assert post(client, "transfers", ["invalid"]).status_code == 400
    csrf_client = APIClient(enforce_csrf_checks=True)
    csrf_client.force_login(user)
    session = csrf_client.session
    session["active_household_id"] = str(home.id)
    session.save()
    assert post(csrf_client, "transactions", payload(home, source)).status_code == 403


def test_postgresql_rejects_foreign_references_even_without_api(context):
    client, user, home, _ = context
    source = account(client)
    other = Household.objects.create(name="Foreign")
    foreign = FinancialAccount.objects.create(household=other, kind="cash", name="Foreign")
    with pytest.raises(IntegrityError), transaction.atomic():
        obj = FinancialTransaction.objects.create(
            household=home,
            creator=user,
            type="opening",
            amount="1",
            account=foreign,
            effective_date=date(2026, 10, 1),
        )
        LedgerEntry.objects.create(
            household=home, transaction=obj, account=foreign, revision=1, amount="1"
        )
        AuditEvent.objects.create(
            household=home,
            actor=user,
            action="opening.create",
            object_type="financialtransaction",
            object_id=obj.pk,
            after={"revision": 1, "status": "posted"},
        )
    assert accounts(home.id).get(pk=source).balance == Decimal("100")
