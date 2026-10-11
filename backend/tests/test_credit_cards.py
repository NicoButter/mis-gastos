from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.categories.services import seed_categories
from apps.credit_cards.models import CardInstallment, CardPurchase, CreditCard
from apps.credit_cards.services import schedule
from apps.households.models import Household, HouseholdMembership
from apps.transactions.models import FinancialTransaction
from apps.transactions.services import accounts
from tests.test_finance import account, post
from tests.test_finance import context as finance_context

context = finance_context


def test_schedule_exact_cents_and_calendar():
    rows = schedule(Decimal("100.00"), 6, date(2026, 1, 25), 25, 10)
    assert [r[0] for r in rows] == [Decimal("16.67")] * 4 + [Decimal("16.66")] * 2
    assert sum(r[0] for r in rows) == Decimal("100")
    assert rows[0][2] == date(2026, 2, 10)
    assert rows[-1][2] == date(2026, 7, 10)
    assert schedule(Decimal("10"), 1, date(2026, 1, 26), 25, 10)[0][2] == date(2026, 3, 10)
    assert schedule(Decimal("10"), 1, date(2028, 2, 29), 31, 31)[0][2] == date(2028, 3, 31)
    assert schedule(Decimal("10"), 1, date(2026, 12, 20), 25, 10)[0][2] == date(2027, 1, 10)
    with pytest.raises(ValidationError):
        schedule(Decimal("0.01"), 6, date(2026, 1, 1), 25, 10)


def card(client):
    response = post(
        client, "credit-cards", {"bank": "Banco", "name": "Visa", "closing_day": 25, "due_day": 10}
    )
    assert response.status_code == 201, response.data
    return response.data["id"]


def purchase(client, home, card_id, key=None):
    return post(
        client,
        "card-purchases",
        {
            "card_id": card_id,
            "category_id": str(Category.objects.filter(household=home, type="expense").first().pk),
            "amount": "100.00",
            "installments_count": 6,
            "purchase_date": "2026-01-20",
            "description": "Heladera",
        },
        key,
    )


@pytest.mark.django_db(transaction=True)
def test_six_installments_full_payment_and_replays(context):
    client, _, home, _ = context
    source = account(client, opening="200")
    card_id = card(client)
    key = uuid4()
    response = purchase(client, home, card_id, key)
    assert response.status_code == 201, response.data
    assert purchase(client, home, card_id, key).status_code == 200
    assert CardPurchase.objects.count() == 1 and CardInstallment.objects.count() == 6
    assert response.data["pending_amount"] == "100.00"
    before = client.get("/api/v1/dashboard/summary/?month=2026-02").data
    assert before["expense"] == "16.67" and before["card_pending"] == "100.00"
    assert before["balance"] == "200.00"
    for row in response.data["installments"]:
        key = uuid4()
        path = f"card-installments/{row['id']}/pay"
        payload = {"account_id": source, "effective_date": row["due_date"]}
        payment = post(client, path, payload, key)
        assert payment.status_code == 200, payment.data
        assert post(client, path, payload, key).data == payment.data
        assert post(client, path, payload).status_code == 409
        assert (
            post(client, path, {**payload, "effective_date": "2026-10-01"}, key).status_code == 409
        )
        op = payment.data["payment_id"]
        assert (
            client.patch(
                f"/api/v1/transactions/{op}/",
                {"amount": "1", "expected_revision": 1},
                format="json",
                HTTP_IDEMPOTENCY_KEY=str(uuid4()),
            ).status_code
            == 400
        )
        assert post(client, f"transactions/{op}/void", {"expected_revision": 1}).status_code == 400
    assert FinancialTransaction.objects.filter(type="card_payment").count() == 6
    assert accounts(home.pk).get(pk=source).balance == Decimal("100.00")
    after = client.get("/api/v1/dashboard/summary/?month=2026-02").data
    assert after["expense"] == "16.67" and after["card_pending"] == "0.00"
    detail = client.get(f"/api/v1/card-purchases/{response.data['id']}/").data
    assert detail["pending_amount"] == "0.00"


@pytest.mark.django_db(transaction=True)
def test_cards_permissions_archival_security_and_tenant(context):
    client, user, home, membership = context
    source = account(client)
    card_id = card(client)
    row = purchase(client, home, card_id).data["installments"][0]

    def patch_card(data):
        return client.patch(
            f"/api/v1/credit-cards/{card_id}/",
            data,
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid4()),
        )

    assert patch_card({"closing_day": 31, "due_day": 31}).status_code == 200
    assert CardInstallment.objects.get(pk=row["id"]).due_date.isoformat() == row["due_date"]
    assert patch_card({"is_active": False}).status_code == 200
    assert purchase(client, home, card_id).status_code == 400
    assert (
        post(client, f"card-installments/{row['id']}/pay", {"account_id": source}).status_code
        == 200
    )
    assert (
        post(
            client,
            "credit-cards",
            {"bank": "B", "name": "N", "closing_day": 0, "due_day": 32, "cvv": "123"},
        ).status_code
        == 400
    )
    other = Household.objects.create(name="Otro")
    HouseholdMembership.objects.create(household=other, user=user, role="owner")
    seed_categories(other.pk)
    session = client.session
    session["active_household_id"] = str(other.pk)
    session.save()
    assert client.get(f"/api/v1/credit-cards/{card_id}/").status_code == 404
    assert purchase(client, other, card_id).status_code == 404
    assert (
        post(client, f"card-installments/{row['id']}/pay", {"account_id": source}).status_code
        == 404
    )
    assert client.get("/api/v1/card-purchases/").data["count"] == 0
    assert client.get("/api/v1/dashboard/summary/").data["card_pending"] == "0.00"
    other_card = card(client)
    installment = purchase(client, other, other_card).data["installments"][0]
    assert (
        post(
            client, f"card-installments/{installment['id']}/pay", {"account_id": source}
        ).status_code
        == 404
    )
    assert client.get("/api/v1/credit-cards/", HTTP_X_HOUSEHOLD_ID=str(home.pk)).status_code == 409
    session = client.session
    session["active_household_id"] = str(home.pk)
    session.save()
    membership.role = "member"
    membership.save()
    assert patch_card({"is_active": True}).status_code == 403
    membership.role = "limited_entry"
    membership.save()
    assert client.get("/api/v1/credit-cards/").status_code == 403
    membership.status = "revoked"
    membership.save()
    assert client.get("/api/v1/credit-cards/").status_code == 404
    anonymous = APIClient()
    assert anonymous.get("/api/v1/credit-cards/").status_code in [401, 403]


@pytest.mark.django_db(transaction=True)
def test_payment_concurrency_atomicity_and_database_guards(context):
    from concurrent.futures import ThreadPoolExecutor
    from unittest.mock import patch

    from django.db import IntegrityError, close_old_connections, transaction

    from apps.transactions.services import write

    client, user, home, _ = context
    source = account(client)
    card_id = card(client)
    row = purchase(client, home, card_id).data["installments"][0]
    data = {"account_id": source, "effective_date": date(2026, 2, 10)}
    with patch("apps.credit_cards.services.audit", side_effect=RuntimeError("audit failure")):
        with pytest.raises(RuntimeError):
            write(user, home.pk, uuid4(), "card_installment.pay", data, row["id"])
    assert FinancialTransaction.objects.filter(type="card_payment").count() == 0
    assert CardInstallment.objects.get(pk=row["id"]).payment_id is None

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
    assert FinancialTransaction.objects.filter(type="card_payment").count() == 1
    with pytest.raises(IntegrityError), transaction.atomic():
        CardInstallment.objects.filter(pk=row["id"]).update(payment=None)
    other = Household.objects.create(name="Ajeno")
    with pytest.raises(IntegrityError), transaction.atomic():
        CreditCard.objects.filter(pk=card_id).update(household=other)
    with pytest.raises(IntegrityError), transaction.atomic():
        CardPurchase.objects.update(amount=Decimal("1"))


@pytest.mark.django_db(transaction=True)
def test_card_payment_csrf_and_archived_source(context):
    client, user, home, _ = context
    source = account(client)
    card_id = card(client)
    row = purchase(client, home, card_id).data["installments"][0]
    secure = APIClient(enforce_csrf_checks=True)
    secure.force_login(user)
    session = secure.session
    session["active_household_id"] = str(home.pk)
    session.save()
    assert (
        post(secure, f"card-installments/{row['id']}/pay", {"account_id": source}).status_code
        == 403
    )
    client.patch(
        f"/api/v1/accounts/{source}/",
        {"is_active": False},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert (
        post(client, f"card-installments/{row['id']}/pay", {"account_id": source}).status_code
        == 400
    )
    assert CardInstallment.objects.get(pk=row["id"]).payment_id is None
