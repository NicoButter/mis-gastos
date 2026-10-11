from __future__ import annotations

import copy

# Keep adversarial SQL statements intact in database-constraint tests.
# ruff: noqa: E501
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import psycopg
import pytest

from tools.ledger_migration_poc import SCHEMA, load_target, reconcile, reset_schema, run, transform

DSN = os.getenv("GASTIO_POC_TEST_DSN", "")
pytestmark = pytest.mark.skipif(not DSN, reason="requires dedicated PostgreSQL POC database")


def uid(label):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"gastio-poc:{label}"))


def snapshot(kind, amount, account, category=None, destination=None, when="2026-02-10", revision=1):
    return {
        "type": kind,
        "amount": str(amount),
        "account": account,
        "destination": destination,
        "category": category,
        "effective_date": when,
        "revision": revision,
        "status": "posted",
    }


def operation(
    label,
    kind,
    amount,
    account,
    category=None,
    destination=None,
    when="2026-02-10",
    updates=(),
    void=False,
    home=None,
):
    op_id, home = uid(label), home or uid("home-a")
    states = [snapshot(kind, amount, account, category, destination, when)]
    for change in updates:
        states.append({**states[-1], **change, "revision": len(states) + 1, "status": "posted"})
    events, lines = [], []
    for i, state in enumerate(states):
        action = "transaction.create" if i == 0 else "transaction.update"
        events.append(
            {
                "id": uid(f"{label}-event-{i+1}"),
                "action": action,
                "before": {} if i == 0 else states[i - 1],
                "after": state,
                "created_at": f"2026-03-{10+i:02}T12:00:00+00:00",
            }
        )
        amount_d = Decimal(state["amount"])
        if state["type"] in {"opening", "income"}:
            deltas = {state["account"]: amount_d}
        elif state["type"] == "expense":
            deltas = {state["account"]: -amount_d}
        else:
            deltas = {state["account"]: -amount_d, state["destination"]: amount_d}
        lines.extend(
            {
                "id": uid(f"{label}-entry-{i+1}-{acct}"),
                "household_id": home,
                "account_id": acct,
                "revision": i + 1,
                "amount": str(delta),
            }
            for acct, delta in deltas.items()
        )
    status = "posted"
    if void:
        state = states[-1]
        voided = {**state, "status": "voided"}
        events.append(
            {
                "id": uid(f"{label}-event-void"),
                "action": "transaction.void",
                "before": state,
                "after": voided,
                "created_at": "2026-03-20T12:00:00+00:00",
            }
        )
        status = "voided"
    final = states[-1]
    current = {
        "id": op_id,
        "household_id": home,
        "type": final["type"],
        "amount": final["amount"],
        "account_id": final["account"],
        "destination_id": final["destination"],
        "category_id": final["category"],
        "effective_date": final["effective_date"],
        "revision": final["revision"],
        "status": status,
        "audit_events": events,
        "ledger_entries": lines,
    }
    return current


@pytest.fixture
def source():
    home_a, home_b = uid("home-a"), uid("home-b")
    acc1, acc2, acc3 = uid("cash-a"), uid("bank-a"), uid("cash-b")
    cat_in, cat_food, cat_other = uid("salary"), uid("food"), uid("other")
    cat_in_b = uid("salary-b")
    ops = [
        operation("opening", "opening", "100000.00", acc1, when="2025-12-01"),
        operation("income", "income", "1234.56", acc1, cat_in, when="2026-01-03"),
        operation(
            "expense",
            "expense",
            "25.01",
            acc1,
            cat_food,
            when="2026-01-11",
            updates=(
                {"amount": "26.02"},
                {"category": cat_other, "account": acc2, "effective_date": "2026-02-03"},
            ),
        ),
        operation("transfer", "transfer", "10.01", acc1, destination=acc2, when="2026-02-04"),
        operation("void", "expense", "5.00", acc1, cat_food, void=True),
        operation(
            "void-corrected",
            "income",
            "7.11",
            acc1,
            cat_in,
            updates=({"amount": "9.99"},),
            void=True,
        ),
        operation("retro", "expense", "0.03", acc1, cat_food, when="2024-06-30"),
        operation("other-home", "income", "88.88", acc3, cat_in_b, home=home_b),
    ]
    return {
        "format_version": 1,
        "receipt_count": 4,
        "households": [{"id": home_a}, {"id": home_b}],
        "accounts": [
            {"id": acc1, "household_id": home_a, "currency": "ARS", "is_active": True},
            {"id": acc2, "household_id": home_a, "currency": "ARS", "is_active": False},
            {"id": acc3, "household_id": home_b, "currency": "ARS", "is_active": True},
        ],
        "categories": [
            {"id": cat_in, "household_id": home_a, "type": "income", "is_active": False},
            {"id": cat_in_b, "household_id": home_b, "type": "income", "is_active": True},
            {"id": cat_food, "household_id": home_a, "type": "expense", "is_active": True},
            {"id": cat_other, "household_id": home_a, "type": "expense", "is_active": False},
        ],
        "operations": ops,
    }


def target():
    return psycopg.connect(DSN, autocommit=True)


def test_transform_covers_revisions_and_is_deterministic(source):
    result = transform(source)
    again = transform(source)
    assert result["exceptions"] == []
    assert [(e["id"], e["lines"]) for e in result["entries"]] == [
        (e["id"], e["lines"]) for e in again["entries"]
    ]
    assert len(result["entries"]) == 16
    assert all(
        sum(line["debit"] for line in e["lines"]) == sum(line["credit"] for line in e["lines"])
        for e in result["entries"]
    )
    assert all(len(e["lines"]) >= 2 for e in result["entries"])
    transfers = [e for e in result["entries"] if e["operation_type"] == "transfer"]
    assert all(
        not any(line["kind"] in {"income", "expense"} for line in e["lines"]) for e in transfers
    )


def test_postgres_load_is_balanced_and_idempotent(source):
    result = transform(source)
    with target() as conn:
        reset_schema(conn)
        load_target(conn, result)
        before = conn.execute(f"select count(*) from {SCHEMA}.journal_entry").fetchone()[0]
        load_target(conn, result)
        after = conn.execute(f"select count(*) from {SCHEMA}.journal_entry").fetchone()[0]
        assert before == after == len(result["entries"])
        assert conn.execute(f"select count(*) from {SCHEMA}.posting").fetchone()[0] == sum(
            len(e["lines"]) for e in result["entries"]
        )
        assert (
            conn.execute(
                f"select count(*) from {SCHEMA}.journal_entry where not posted"
            ).fetchone()[0]
            == 0
        )
        assert reconcile(source, result, conn) == []
        changed = copy.deepcopy(source)
        changed["accounts"][0]["is_active"] = not changed["accounts"][0]["is_active"]
        with pytest.raises(ValueError, match="IDEMPOTENCY_SOURCE_ACCOUNT_MISMATCH"):
            load_target(conn, transform(changed))
        assert conn.execute(f"select count(*) from {SCHEMA}.journal_entry").fetchone()[0] == before


def test_interrupt_rolls_back_and_rerun_completes(source):
    result = transform(source)
    with target() as conn:
        reset_schema(conn)
        with pytest.raises(RuntimeError, match="SIMULATED_INTERRUPTION"):
            load_target(conn, result, fail_after=3)
        assert conn.execute(f"select count(*) from {SCHEMA}.journal_entry").fetchone()[0] == 0
        load_target(conn, result)
        assert conn.execute(f"select count(*) from {SCHEMA}.journal_entry").fetchone()[0] == len(
            result["entries"]
        )


def test_database_rejects_imbalanced_and_incomplete_postings(source):
    result = transform(source)
    with target() as conn:
        reset_schema(conn)
        # A staged, incomplete entry cannot be sealed/committed as a valid journal.
        home = next(iter(result["households"]))
        entry = uid("bad-entry")
        source_op, source_event = uid("bad-op"), uid("bad-event")
        conn.execute(
            f"insert into {SCHEMA}.household(id) values (%s) on conflict do nothing", (home,)
        )
        conn.execute(
            f"insert into {SCHEMA}.source_operation(id,household_id,current_revision,status) values (%s,%s,1,'posted')",
            (source_op, home),
        )
        conn.execute(
            f"insert into {SCHEMA}.source_audit_event(id,household_id,operation_id,action,before_snapshot,after_snapshot,recorded_at) values (%s,%s,%s,'transaction.create','{{}}','{{}}',now())",
            (source_event, home, source_op),
        )
        with pytest.raises(psycopg.errors.CheckViolation):
            with conn.transaction():
                conn.execute(
                    f"insert into {SCHEMA}.journal_entry(id,household_id,source_operation_id,source_revision,purpose,source_audit_event_id,effective_date,recorded_at,currency,operation_type,posted) values (%s,%s,%s,1,'effect',%s,'2026-01-01',now(),'ARS','expense',false)",
                    (entry, home, source_op, source_event),
                )
                conn.execute(f"update {SCHEMA}.journal_entry set posted=true where id=%s", (entry,))
                conn.execute(
                    f"insert into {SCHEMA}.ledger_account(id,household_id,kind,currency) values (%s,%s,'asset','ARS')",
                    (uid("bad-account"), home),
                )
                conn.execute(
                    f"insert into {SCHEMA}.posting(household_id,entry_id,ledger_account_id,line_no,debit,currency,operation_type,effective_date) values (%s,%s,%s,1,1,'ARS','expense','2026-01-01')",
                    (home, entry, uid("bad-account")),
                )


def test_multitenant_reference_is_an_explicit_exception(source):
    source["operations"].append(
        operation("cross-home", "expense", "1.00", uid("cash-b"), uid("food"), home=uid("home-a"))
    )
    result = transform(source)
    assert result["entries"] == []
    assert "CROSS_HOUSEHOLD_ACCOUNT" in result["exceptions"]


def test_ledger_and_audit_rows_cannot_claim_another_household(source):
    bad_ledger = copy.deepcopy(source)
    bad_ledger["operations"][0]["ledger_entries"][0]["household_id"] = uid("home-b")
    assert "CROSS_HOUSEHOLD_LEDGER_ENTRY" in transform(bad_ledger)["exceptions"]
    bad_audit = copy.deepcopy(source)
    bad_audit["operations"][0]["audit_events"][0]["household_id"] = uid("home-b")
    assert "CROSS_HOUSEHOLD_AUDIT_EVENT" in transform(bad_audit)["exceptions"]


def test_concurrent_replay_has_no_duplicate_entries(source):
    result = transform(source)
    with target() as conn:
        reset_schema(conn)

    def write():
        with target() as conn:
            load_target(conn, result)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: write(), range(2)))
    with target() as conn:
        assert conn.execute(f"select count(*) from {SCHEMA}.journal_entry").fetchone()[0] == len(
            result["entries"]
        )


def test_audit_gap_fails_closed(source):
    source["operations"][0]["audit_events"] = []
    result = transform(source)
    assert result["entries"] == []
    assert "MISSING_AUDIT_CHAIN" in result["exceptions"]


def test_incomplete_historical_snapshot_is_never_filled_from_current_row(source):
    source["operations"][2]["audit_events"][0]["after"].pop("amount")
    result = transform(source)
    assert result["entries"] == []
    assert "INCOMPLETE_FINANCIAL_SNAPSHOT" in result["exceptions"]


def test_machine_report_is_pass_and_contains_no_personal_fields(source, tmp_path):
    input_path = tmp_path / "synthetic.json"
    report_path = tmp_path / "report.json"
    input_path.write_text(json.dumps(source))
    dsn = DSN
    report = run(input_path, report_path, dsn, reset=True)
    assert report["status"] == "PASS"
    assert report["reconciled"] is True
    assert report["balanced"] is True
    assert report["coverage_complete"] is True
    assert report["historical_cuts"] == 4
    assert report["historical_cut_differences"] == []
    assert report["receipts"] == 4
    assert report["revisions"] == 11
    assert report["audit_events"] == 13
    serialized = report_path.read_text()
    assert "email" not in serialized and "description" not in serialized


def test_interrupted_report_is_incomplete_never_pass(source, tmp_path):
    input_path = tmp_path / "synthetic.json"
    report_path = tmp_path / "incomplete.json"
    input_path.write_text(json.dumps(source))
    report = run(input_path, report_path, DSN, reset=True, fail_after=2)
    assert report["status"] == "INCOMPLETE"
    assert report["reconciled"] is False
    with target() as conn:
        assert conn.execute(f"select count(*) from {SCHEMA}.journal_entry").fetchone()[0] == 0
