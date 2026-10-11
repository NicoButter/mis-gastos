from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest

from apps.households.models import Household, HouseholdMembership
from tests.test_finance import account, payload, post
from tests.test_finance import context as finance_context

context = finance_context
pytestmark = pytest.mark.django_db(transaction=True)


def test_monthly_account_flows_and_liquid_available_balance(context):
    client, _, home, _ = context
    source = account(client, "Efectivo", "100.25")  # opening in September
    target = account(client, "Banco", "0")
    empty = account(client, "Sin movimientos", "0")
    archived = account(client, "Archivada", "500")
    other = post(
        client,
        "accounts",
        {
            "name": "No líquida",
            "kind": "other",
            "opening_balance": "700",
            "opening_date": "2026-10-01",
        },
    ).data["id"]
    client.patch(
        f"/api/v1/accounts/{archived}/",
        {"is_active": False},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    for kind, amount, extra in [
        ("income", "50.10", {}),
        ("expense", "20.05", {}),
        ("transfer", "30.00", {"destination_id": target}),
        ("income", "40.00", {"effective_date": "2026-09-30"}),
        ("expense", "80.00", {"effective_date": "2026-11-01"}),
    ]:
        assert (
            post(client, "transactions", payload(home, source, kind, amount, **extra)).status_code
            == 201
        )
    summary = client.get("/api/v1/dashboard/summary/?month=2026-10").data
    assert summary["available_balances"] == [{"currency": "ARS", "amount": "90.30"}]
    assert summary["balance"] == "1290.30"  # compatibility: includes archived/other
    assert (summary["income"], summary["expense"], summary["net"]) == ("50.10", "20.05", "30.05")
    rows = {row["id"]: row for row in summary["accounts"]}
    assert rows[source]["month"] == "2026-10"
    assert rows[source]["balance"] == "60.30"
    assert rows[source]["monthly_inflow"] == "50.10"
    assert rows[source]["monthly_income"] == "50.10"
    assert rows[source]["monthly_outflow"] == "50.05"
    assert rows[source]["monthly_expense"] == "20.05"
    assert rows[source]["monthly_transfer_out"] == "30.00"
    assert rows[target]["monthly_inflow"] == "30.00"
    assert rows[target]["monthly_income"] == "0.00"
    assert rows[target]["monthly_transfer_in"] == "30.00"
    assert rows[empty]["balance"] == "0.00"
    assert rows[empty]["monthly_inflow"] == rows[empty]["monthly_outflow"] == "0.00"
    assert rows[other]["monthly_opening"] == rows[other]["monthly_inflow"] == "700.00"
    assert rows[other]["monthly_income"] == "0.00"
    detail = client.get(f"/api/v1/accounts/{source}/?month=2026-10").data
    assert {key: value for key, value in detail.items() if key != "usage_count"} == {
        key: value for key, value in rows[source].items() if key != "usage_count"
    }
    september = client.get(f"/api/v1/accounts/{source}/?month=2026-09").data
    assert september["monthly_opening"] == "100.25"
    assert september["monthly_inflow"] == "140.25"
    assert september["monthly_income"] == "40.00"
    assert september["balance"] == "60.30"
    november = client.get("/api/v1/dashboard/summary/?month=2026-11").data
    assert november["available_balances"] == summary["available_balances"]
    assert (november["income"], november["expense"], november["net"]) == ("0.00", "80.00", "-80.00")


def test_kpis_reflect_corrections_voids_archival_and_household(context):
    client, user, home, _ = context
    source = account(client, opening="10.00")
    income = post(client, "transactions", payload(home, source, "income", "100.01")).data
    expense = post(client, "transactions", payload(home, source, "expense", "20.02")).data
    response = client.patch(
        f"/api/v1/transactions/{expense['id']}/",
        {"amount": "30.03", "expected_revision": 1},
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid4()),
    )
    assert response.status_code == 200
    assert (
        post(client, f"transactions/{income['id']}/void", {"expected_revision": 1}).status_code
        == 200
    )
    summary = client.get("/api/v1/dashboard/summary/?month=2026-10").data
    assert (summary["income"], summary["expense"], summary["net"]) == ("0.00", "30.03", "-30.03")
    assert summary["available_balances"][0]["amount"] == "-20.03"
    source_data = client.get(f"/api/v1/accounts/{source}/?month=2026-10").data
    assert source_data["monthly_income"] == source_data["monthly_inflow"] == "0.00"
    assert source_data["monthly_outflow"] == source_data["monthly_expense"] == "30.03"
    assert (
        post(client, f"transactions/{expense['id']}/void", {"expected_revision": 2}).status_code
        == 200
    )
    assert client.get("/api/v1/dashboard/summary/?month=2026-10").data["expense"] == "0.00"
    other = Household.objects.create(name="Otro hogar")
    HouseholdMembership.objects.create(user=user, household=other, role="owner")
    session = client.session
    session["active_household_id"] = str(other.pk)
    session.save()
    summary = client.get("/api/v1/dashboard/summary/?month=2026-10").data
    assert summary["available_balances"] == [{"currency": "ARS", "amount": "0.00"}]
    assert summary["accounts"] == []
    assert summary["income"] == summary["expense"] == summary["net"] == "0.00"
    assert client.get(f"/api/v1/accounts/{source}/?month=2026-10").status_code == 404
    assert client.get("/api/v1/accounts/?month=2026-10").data["results"] == []


def test_card_payment_is_outflow_not_a_second_expense(context):
    from tests.test_credit_cards import card, purchase

    client, _, home, _ = context
    source = account(client, opening="200")
    row = purchase(client, home, card(client)).data["installments"][0]
    assert (
        post(
            client,
            f"card-installments/{row['id']}/pay",
            {"account_id": source, "effective_date": "2026-03-01"},
        ).status_code
        == 200
    )
    february = client.get("/api/v1/dashboard/summary/?month=2026-02").data
    march = client.get("/api/v1/dashboard/summary/?month=2026-03").data
    assert february["expense"] == march["expense"] == "16.67"  # purchase installments only
    details = client.get(f"/api/v1/accounts/{source}/?month=2026-03").data
    assert details["monthly_card_payments"] == details["monthly_outflow"] == "16.67"
    assert details["monthly_income"] == details["monthly_expense"] == "0.00"
    assert details["balance"] == february["available_balances"][0]["amount"] == "183.33"


def test_period_defaults_validation_and_decimal_precision(context):
    client, _, _, _ = context
    source = account(client, opening="9999999999999999.99")
    with patch("apps.transactions.services.timezone.localdate", return_value=date(2026, 12, 31)):
        assert client.get("/api/v1/dashboard/summary/").data["month"] == "2026-12"
        assert client.get(f"/api/v1/accounts/{source}/").data["month"] == "2026-12"
    summary = client.get("/api/v1/dashboard/summary/?month=2026-09").data
    assert summary["available_balances"][0]["amount"] == "9999999999999999.99"
    assert Decimal(summary["income"]) == 0  # opening is not income
    for month in ["2026-13", "2026-00", "2026-1", "bad", "0000-01", "9999-12", ""]:
        assert client.get("/api/v1/dashboard/summary/", {"month": month}).status_code == 400
        assert client.get("/api/v1/accounts/", {"month": month}).status_code == 400
