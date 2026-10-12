from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import IntegrityError, close_old_connections, transaction

from apps.categories.models import Category
from apps.categories.services import seed_categories
from apps.credit_cards.models import CardInstallment, CardPurchase, InstallmentPayment
from apps.households.models import Household, HouseholdMembership
from apps.recurring.models import RecurringExpense, RecurringOccurrence
from apps.transactions.models import FinancialTransaction
from apps.transactions.services import accounts, write
from tests.test_finance import account, post
from tests.test_finance import context as finance_context

context = finance_context
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def current_date():
    with patch("apps.recurring.services.timezone.localdate", return_value=date(2026, 10, 10)):
        yield


def financed(client, home, key=None, **extra):
    return post(
        client,
        "card-purchases",
        {
            "description": "Bicicleta",
            "amount": "100.00",
            "installments_count": 3,
            "first_due_date": "2026-10-31",
            "creditor": "Bicicletería",
            "category_id": str(Category.objects.filter(household=home, type="expense").first().pk),
            **extra,
        },
        key,
    )


def recurring(client, home, source=None, key=None, **extra):
    return post(
        client,
        "recurring-expenses",
        {
            "name": "Netflix",
            "amount": "10.00",
            "start_date": "2026-10-01",
            "due_day": 15,
            "category_id": str(Category.objects.filter(household=home, type="expense").first().pk),
            "account_id": source,
            **extra,
        },
        key,
    )


def patch_api(client, path, data, key=None):
    return client.patch(
        f"/api/v1/{path}/", data, format="json", HTTP_IDEMPOTENCY_KEY=str(key or uuid4())
    )


def test_financed_calendar_partial_payments_and_no_duplicate_expense(context):
    client, _, home, _ = context
    source = account(client, opening="200.00")
    key = uuid4()
    purchase = financed(client, home, key)
    assert purchase.status_code == 201, purchase.data
    assert financed(client, home, key).status_code == 200
    assert CardPurchase.objects.count() == 1 and CardInstallment.objects.count() == 3
    rows = purchase.data["installments"]
    assert [r["amount"] for r in rows] == ["33.34", "33.33", "33.33"]
    assert [r["due_date"] for r in rows] == ["2026-10-31", "2026-11-30", "2026-12-31"]
    assert rows[0]["closing_date"] is None and rows[0]["card_name"] is None
    assert accounts(home.pk).get(pk=source).balance == Decimal("200.00")
    path = f"card-installments/{rows[0]['id']}/pay"
    key = uuid4()
    payload = {"account_id": source, "amount": "20.00", "effective_date": "2026-10-12"}
    paid = post(client, path, payload, key)
    assert paid.status_code == 200, paid.data
    assert paid.data["paid_amount"] == "20.00" and paid.data["pending_amount"] == "13.34"
    assert paid.data["status"] == "partial"
    assert post(client, path, payload, key).data == paid.data
    assert post(client, path, {**payload, "amount": "19.00"}, key).status_code == 409
    assert post(client, path, payload).status_code == 400
    completed = post(
        client, path, {"account_id": source, "amount": "13.34", "effective_date": "2026-10-13"}
    )
    assert completed.data["status"] == "paid" and completed.data["pending_amount"] == "0.00"
    assert len(completed.data["payments"]) == 2
    assert post(client, path, payload).status_code == 409
    summary = client.get("/api/v1/dashboard/summary/?month=2026-10").data
    assert (
        summary["expense"] == "33.34"
    )  # two payment records must not multiply the purchase expense
    assert summary["card_pending"] == "66.66"
    assert summary["available_balances"][0]["amount"] == "166.66"
    assert (
        client.get(f"/api/v1/card-purchases/{purchase.data['id']}/").data["pending_amount"]
        == "66.66"
    )
    assert InstallmentPayment.objects.count() == 2
    for row in rows[1:]:
        assert (
            post(client, f"card-installments/{row['id']}/pay", {"account_id": source}).status_code
            == 200
        )
    assert client.get("/api/v1/dashboard/summary/").data["card_pending"] == "0.00"
    assert accounts(home.pk).get(pk=source).balance == Decimal("100.00")


def test_recurrence_only_records_expense_on_confirmation_and_changes_one_occurrence(context):
    client, _, home, _ = context
    source = account(client, opening="100.00")
    key = uuid4()
    response = recurring(client, home, source, key)
    assert response.status_code == 201, response.data
    assert recurring(client, home, source, key).status_code == 200
    assert RecurringExpense.objects.count() == 1
    assert len(response.data["occurrences"]) == 3
    row = response.data["occurrences"][0]
    before_count = RecurringOccurrence.objects.count()
    assert client.get("/api/v1/recurring-expenses/").status_code == 200
    assert client.get("/api/v1/recurring-occurrences/").status_code == 200
    assert RecurringOccurrence.objects.count() == before_count
    summary = client.get("/api/v1/dashboard/summary/?month=2026-10").data
    assert summary["expense"] == "0.00" and summary["available_balances"][0]["amount"] == "100.00"
    assert summary["upcoming_recurring"][0]["name"] == "Netflix"
    updated = patch_api(client, f"recurring-occurrences/{row['id']}", {"amount": "13.05"})
    assert updated.status_code == 200, updated.data
    assert RecurringOccurrence.objects.exclude(pk=row["id"]).first().amount == Decimal("10.00")
    key = uuid4()
    paid = post(
        client, f"recurring-occurrences/{row['id']}/pay", {"effective_date": "2026-10-15"}, key
    )
    assert paid.status_code == 200, paid.data
    assert paid.data["status"] == "paid"
    assert (
        post(
            client, f"recurring-occurrences/{row['id']}/pay", {"effective_date": "2026-10-15"}, key
        ).data
        == paid.data
    )
    assert post(client, f"recurring-occurrences/{row['id']}/pay", {}).status_code == 409
    assert (
        patch_api(client, f"recurring-occurrences/{row['id']}", {"amount": "14"}).status_code == 409
    )
    summary = client.get("/api/v1/dashboard/summary/?month=2026-10").data
    assert summary["expense"] == "13.05" and summary["available_balances"][0]["amount"] == "86.95"
    assert FinancialTransaction.objects.filter(type="expense").count() == 1
    payment = paid.data["payment_id"]
    assert (
        patch_api(
            client, f"transactions/{payment}", {"expected_revision": 1, "amount": "1"}
        ).status_code
        == 400
    )
    assert post(client, f"transactions/{payment}/void", {"expected_revision": 1}).status_code == 400
    with pytest.raises(IntegrityError), transaction.atomic():
        FinancialTransaction.objects.filter(pk=payment).update(status="voided")


def test_recurrence_calendar_pause_resume_cancel_and_history(context):
    client, _, home, _ = context
    source = account(client)
    result = recurring(client, home, source, start_date="2026-01-30", due_day=31).data
    assert [r["due_date"] for r in result["occurrences"][:3]] == [
        "2026-01-31",
        "2026-02-28",
        "2026-03-31",
    ]
    rule_id = result["id"]
    first = result["occurrences"][0]["id"]
    assert post(client, f"recurring-occurrences/{first}/pay", {}).status_code == 200
    assert (
        patch_api(client, f"recurring-expenses/{rule_id}", {"status": "paused"}).status_code == 200
    )
    assert RecurringOccurrence.objects.get(pk=first).status == "paid"
    assert not RecurringOccurrence.objects.filter(
        recurring_id=rule_id, due_date__gte=date(2026, 10, 10), status="pending"
    ).exists()
    with patch("apps.recurring.services.timezone.localdate", return_value=date(2027, 2, 10)):
        client.get("/api/v1/recurring-expenses/")
        assert not RecurringOccurrence.objects.filter(due_date__year=2027).exists()
        assert (
            patch_api(client, f"recurring-expenses/{rule_id}", {"status": "active"}).status_code
            == 200
        )
        assert RecurringOccurrence.objects.filter(
            due_date=date(2027, 2, 28), status="pending"
        ).exists()
        assert not RecurringOccurrence.objects.filter(due_date=date(2027, 1, 31)).exists()
        assert (
            patch_api(client, f"recurring-expenses/{rule_id}", {"status": "cancelled"}).status_code
            == 200
        )
        assert (
            patch_api(client, f"recurring-expenses/{rule_id}", {"status": "active"}).status_code
            == 409
        )
        assert (
            client.get(f"/api/v1/recurring-expenses/{rule_id}/").data["occurrences"][0]["status"]
            == "paid"
        )


def test_commitments_isolation_roles_and_archived_accounts(context):
    client, user, home, membership = context
    source = account(client)
    purchase = financed(client, home).data
    recurrence = recurring(client, home, source).data
    other = Household.objects.create(name="Ajeno")
    HouseholdMembership.objects.create(household=other, user=user, role="owner")
    seed_categories(other.pk)
    session = client.session
    session["active_household_id"] = str(other.pk)
    session.save()
    assert client.get(f"/api/v1/card-purchases/{purchase['id']}/").status_code == 404
    assert client.get(f"/api/v1/recurring-expenses/{recurrence['id']}/").status_code == 404
    assert (
        post(
            client,
            f"card-installments/{purchase['installments'][0]['id']}/pay",
            {"account_id": source},
        ).status_code
        == 404
    )
    assert (
        post(
            client, f"recurring-occurrences/{recurrence['occurrences'][0]['id']}/pay", {}
        ).status_code
        == 404
    )
    assert recurring(client, other, source).status_code == 404
    foreign_purchase = financed(client, other).data
    assert (
        post(
            client,
            f"card-installments/{foreign_purchase['installments'][0]['id']}/pay",
            {"account_id": source},
        ).status_code
        == 404
    )
    assert client.get("/api/v1/dashboard/summary/").data["upcoming_recurring"] == []
    session = client.session
    session["active_household_id"] = str(home.pk)
    session.save()
    patch_api(client, f"accounts/{source}", {"is_active": False})
    assert (
        post(
            client,
            f"card-installments/{purchase['installments'][0]['id']}/pay",
            {"account_id": source},
        ).status_code
        == 400
    )
    assert (
        post(
            client, f"recurring-occurrences/{recurrence['occurrences'][0]['id']}/pay", {}
        ).status_code
        == 400
    )
    membership.role = "limited_entry"
    membership.save()
    assert client.get("/api/v1/recurring-expenses/").status_code == 403
    assert financed(client, home).status_code == 403


def test_partial_payment_concurrency_and_atomicity(context):
    client, user, home, _ = context
    source = account(client)
    row = financed(client, home).data["installments"][0]
    data = {"account_id": source, "amount": Decimal("20.00"), "effective_date": date(2026, 10, 10)}
    with patch("apps.credit_cards.services.audit", side_effect=RuntimeError("audit failed")):
        with pytest.raises(RuntimeError):
            write(user, home.pk, uuid4(), "card_installment.pay", data, row["id"])
    assert InstallmentPayment.objects.count() == 0
    key = uuid4()

    def pay():
        close_old_connections()
        try:
            return write(user, home.pk, key, "card_installment.pay", data, row["id"])
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: pay(), range(2)))
    assert sorted(result[1] for result in results) == [False, True]
    assert InstallmentPayment.objects.count() == 1
    assert accounts(home.pk).get(pk=source).balance == Decimal("80.00")


def test_recurring_concurrency_and_empty_patch_validation(context):
    client, user, home, _ = context
    source = account(client)
    result = recurring(client, home, source).data
    row = result["occurrences"][0]
    assert patch_api(client, f"recurring-expenses/{result['id']}", {}).status_code == 400
    assert patch_api(client, f"recurring-occurrences/{row['id']}", {}).status_code == 400
    key = uuid4()

    def pay():
        close_old_connections()
        try:
            return write(
                user,
                home.pk,
                key,
                "recurring_occurrence.pay",
                {"effective_date": date(2026, 10, 15)},
                row["id"],
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: pay(), range(2)))
    assert sorted(result[1] for result in results) == [False, True]
    assert FinancialTransaction.objects.filter(type="expense").count() == 1
    with pytest.raises(IntegrityError), transaction.atomic():
        RecurringOccurrence.objects.filter(pk=row["id"]).update(amount=1)


def test_invalid_financing_and_recurring_fields(context):
    client, _, home, _ = context
    assert financed(client, home, first_due_date=None).status_code == 400
    assert financed(client, home, frequency="weekly").status_code == 400
    assert financed(client, home, amount="0.01", installments_count=3).status_code == 400
    assert recurring(client, home, due_day=32).status_code == 400
    assert recurring(client, home, frequency="weekly").status_code == 400
    assert recurring(client, home, amount="0").status_code == 400
