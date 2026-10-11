"""Read-only exporter for an isolated ledger POC source snapshot.

Use a PostgreSQL role with SELECT-only grants. Output contains financial values and
UUIDs, so write it outside the repository and protect/delete it after validation.
"""
# SQL statements are kept as table/column clauses for reviewability.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

FINANCIAL_FIELDS = (
    "id",
    "household_id",
    "type",
    "amount",
    "currency",
    "effective_date",
    "account_id",
    "destination_id",
    "category_id",
    "status",
    "revision",
)
SNAPSHOT_FIELDS = (
    "type",
    "amount",
    "effective_date",
    "account",
    "account_id",
    "destination",
    "destination_id",
    "category",
    "category_id",
    "status",
    "revision",
)


def json_value(value):
    if isinstance(value, Decimal | date | datetime):
        return str(value)
    return value


def clean_snapshot(value):
    if not isinstance(value, dict):
        return {}
    # Deliberately discard actor IDs, household names, descriptions, notes and PII.
    return {key: json_value(value[key]) for key in SNAPSHOT_FIELDS if key in value}


def export(dsn: str, destination: Path):
    if destination.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("SNAPSHOT_MUST_BE_OUTSIDE_REPOSITORY")
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '120s'")
            households = conn.execute("SELECT id FROM households_household ORDER BY id").fetchall()
            accounts = conn.execute(
                "SELECT id,household_id,currency,is_active FROM wallets_financialaccount ORDER BY id"
            ).fetchall()
            categories = conn.execute(
                "SELECT id,household_id,type,is_active FROM categories_category ORDER BY id"
            ).fetchall()
            operations = conn.execute(
                f"SELECT {','.join(FINANCIAL_FIELDS)},created_at,updated_at FROM transactions_financialtransaction ORDER BY id"
            ).fetchall()
            ledgers = conn.execute(
                "SELECT id,household_id,transaction_id,account_id,revision,amount FROM transactions_ledgerentry ORDER BY transaction_id,revision,account_id"
            ).fetchall()
            audits = conn.execute(
                "SELECT id,household_id,actor_id,action,object_type,object_id,before,after,created_at FROM audit_auditevent WHERE object_type='financialtransaction' ORDER BY object_id,created_at,id"
            ).fetchall()
            receipt_count = conn.execute(
                "SELECT count(*) AS n FROM transactions_writereceipt"
            ).fetchone()["n"]
        by_op = {}
        for audit in audits:
            event = {
                "id": str(audit["id"]),
                "household_id": str(audit["household_id"]),
                "actor_id": str(audit["actor_id"]),
                "action": audit["action"],
                "before": clean_snapshot(audit["before"]),
                "after": clean_snapshot(audit["after"]),
                "created_at": audit["created_at"].isoformat(),
            }
            by_op.setdefault(str(audit["object_id"]), []).append(event)
        ledger_by_op = {}
        for row in ledgers:
            ledger_by_op.setdefault(str(row["transaction_id"]), []).append(
                {
                    "id": str(row["id"]),
                    "household_id": str(row["household_id"]),
                    "account_id": str(row["account_id"]),
                    "revision": row["revision"],
                    "amount": str(row["amount"]),
                }
            )
        operation_rows = []
        for row in operations:
            item = {k: json_value(row[k]) for k in FINANCIAL_FIELDS}
            item["id"] = str(item["id"])
            item["household_id"] = str(item["household_id"])
            for key in ("account_id", "destination_id", "category_id"):
                item[key] = str(item[key]) if item[key] is not None else None
            item["audit_events"] = by_op.get(item["id"], [])
            item["ledger_entries"] = ledger_by_op.get(item["id"], [])
            operation_rows.append(item)
        snapshot = {
            "format_version": 1,
            "source_schema": "gastio-phase1-financial-v1",
            "receipt_count": receipt_count,
            "households": [{"id": str(row["id"])} for row in households],
            "accounts": [
                {
                    "id": str(r["id"]),
                    "household_id": str(r["household_id"]),
                    "currency": r["currency"],
                    "is_active": r["is_active"],
                }
                for r in accounts
            ],
            "categories": [
                {
                    "id": str(r["id"]),
                    "household_id": str(r["household_id"]),
                    "type": r["type"],
                    "is_active": r["is_active"],
                }
                for r in categories
            ],
            "operations": operation_rows,
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(snapshot, default=json_value, indent=2) + "\n")
    return {
        "households": len(households),
        "accounts": len(accounts),
        "categories": len(categories),
        "operations": len(operations),
        "revisions": sum(len(op["audit_events"]) for op in operation_rows),
        "receipts": receipt_count,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dsn-env", default="GASTIO_SOURCE_RO_DSN")
    args = parser.parse_args(argv)
    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        parser.error(f"Set {args.dsn_env} to a read-only PostgreSQL connection string")
    try:
        counts = export(dsn, args.output)
    except Exception as exc:
        code = str(exc) if str(exc).isupper() else "EXPORT_FAILED"
        print(json.dumps({"status": "FAIL", "error_code": code}), file=sys.stderr)
        return 1
    print(json.dumps({"status": "EXPORTED", "output": str(args.output), **counts}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
