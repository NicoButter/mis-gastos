"""Opt-in reproducible measurements, only inside pytest's disposable database."""

import json
import os
import statistics
from datetime import date
from decimal import Decimal
from pathlib import Path
from time import perf_counter

import pytest
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditEvent
from apps.categories.models import Category
from apps.categories.services import seed_categories
from apps.households.models import Household, HouseholdMembership
from apps.transactions.models import FinancialTransaction, LedgerEntry
from apps.transactions.services import accounts, operations
from apps.wallets.models import FinancialAccount

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(os.getenv("GASTIO_BENCHMARK") != "1", reason="Opt-in synthetic benchmark"),
]


def test_synthetic_financial_query_scaling():
    user = User.objects.create_user("benchmark@synthetic.invalid")
    home = Household.objects.create(name="Synthetic benchmark")
    HouseholdMembership.objects.create(user=user, household=home, role="owner")
    seed_categories(home.pk)
    wallet = FinancialAccount.objects.create(household=home, name="Synthetic", kind="cash")
    category = Category.objects.filter(household=home, type="expense").first()
    client = APIClient()
    client.force_login(user)
    session = client.session
    session["active_household_id"] = str(home.pk)
    session.save()
    reports = []
    counts = {}
    for size, added in [(100, 100), (10000, 9900)]:
        with transaction.atomic():
            batch = [
                FinancialTransaction(
                    household=home,
                    creator=user,
                    type="expense",
                    account=wallet,
                    category=category,
                    amount=Decimal("1.25"),
                    effective_date=date(2026, 10, 1 + i % 28),
                )
                for i in range(added)
            ]
            FinancialTransaction.objects.bulk_create(batch)
            LedgerEntry.objects.bulk_create(
                [
                    LedgerEntry(
                        household=home,
                        transaction=op,
                        account=wallet,
                        revision=1,
                        amount=Decimal("-1.25"),
                    )
                    for op in batch
                ]
            )
            AuditEvent.objects.bulk_create(
                [
                    AuditEvent(
                        household=home,
                        actor=user,
                        action="transaction.create",
                        object_type="financialtransaction",
                        object_id=op.pk,
                        after={"revision": 1, "status": "posted"},
                    )
                    for op in batch
                ]
            )
        assert accounts(home.pk).get(pk=wallet.pk).balance == Decimal("-1.25") * size
        with connection.cursor() as cursor:
            for table in [
                "transactions_financialtransaction",
                "transactions_ledgerentry",
                "wallets_financialaccount",
                "categories_category",
                "accounts_user",
            ]:
                cursor.execute(f"ANALYZE {table}")
        paths = {
            "movements": "/api/v1/transactions/",
            "balances": "/api/v1/accounts/",
            "dashboard": "/api/v1/dashboard/summary/?month=2026-10",
            "date_category": (
                "/api/v1/transactions/?from=2026-10-01&to=2026-10-15" f"&category={category.pk}"
            ),
        }
        for name, path in paths.items():
            assert client.get(path).status_code == 200  # warm cache
            samples, queries = [], []
            for _ in range(20):
                with CaptureQueriesContext(connection) as captured:
                    start = perf_counter()
                    response = client.get(path)
                    samples.append((perf_counter() - start) * 1000)
                assert response.status_code == 200
                queries.append(len(captured))
            reports.append(
                {
                    "rows": size,
                    "endpoint": name,
                    "queries": max(queries),
                    "median_ms": round(statistics.median(samples), 2),
                    "p95_ms": round(sorted(samples)[18], 2),
                }
            )
            if size == 100:
                counts[name] = max(queries)
            else:
                assert max(queries) <= counts[name], "Query count grew with data (possible N+1)"
    plans = {
        "movements": json.loads(
            operations(home.pk).all()[:25].explain(analyze=True, buffers=True, format="json")
        ),
        "balances": json.loads(
            accounts(home.pk).explain(analyze=True, buffers=True, format="json")
        ),
        "date_category": json.loads(
            operations(home.pk)
            .filter(category=category, effective_date__lte=date(2026, 10, 15))[:25]
            .explain(analyze=True, buffers=True, format="json")
        ),
    }
    output = Path(os.getenv("GASTIO_BENCHMARK_OUTPUT", "/tmp/gastio-phase11-benchmark.json"))
    output.write_text(
        json.dumps({"samples_per_endpoint": 20, "measurements": reports, "plans": plans}, indent=2)
    )
    print(json.dumps(reports))
