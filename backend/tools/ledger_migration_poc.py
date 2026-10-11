"""Isolated, deterministic financial-ledger migration proof of concept.

Input is a normalized JSON snapshot. No Gastio ORM model or production table is changed.
"""
# SQL DDL/query literals are kept as clauses, so long embedded lines are intentional.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg

VERSION = "0.1.0"
SCHEMA = "migration_poc"
DB_PREFIX = "gastio_migration_test_"

DDL = f"""
CREATE SCHEMA IF NOT EXISTS {SCHEMA};
CREATE TABLE IF NOT EXISTS {SCHEMA}.household (
  id uuid PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS {SCHEMA}.source_account (
  id uuid NOT NULL,
  household_id uuid NOT NULL REFERENCES {SCHEMA}.household(id),
  currency char(3) NOT NULL CHECK (currency='ARS'),
  is_active boolean NOT NULL,
  PRIMARY KEY(household_id,id), UNIQUE(id)
);
CREATE TABLE IF NOT EXISTS {SCHEMA}.source_category (
  id uuid NOT NULL,
  household_id uuid NOT NULL REFERENCES {SCHEMA}.household(id),
  operation_type text NOT NULL CHECK (operation_type IN ('income','expense')),
  is_active boolean NOT NULL,
  PRIMARY KEY(household_id,id), UNIQUE(id)
);
CREATE TABLE IF NOT EXISTS {SCHEMA}.source_operation (
  id uuid NOT NULL,
  household_id uuid NOT NULL REFERENCES {SCHEMA}.household(id),
  current_revision integer NOT NULL CHECK (current_revision > 0),
  status text NOT NULL CHECK(status IN ('posted','voided')),
  PRIMARY KEY(household_id,id), UNIQUE(id)
);
CREATE TABLE IF NOT EXISTS {SCHEMA}.source_audit_event (
  id uuid NOT NULL,
  household_id uuid NOT NULL,
  operation_id uuid NOT NULL,
  actor_id uuid,
  action text NOT NULL,
  before_snapshot jsonb NOT NULL,
  after_snapshot jsonb NOT NULL,
  recorded_at timestamptz NOT NULL,
  PRIMARY KEY(household_id,id),
  FOREIGN KEY(household_id,operation_id) REFERENCES {SCHEMA}.source_operation(household_id,id)
);
CREATE TABLE IF NOT EXISTS {SCHEMA}.ledger_account (
  id uuid PRIMARY KEY,
  household_id uuid NOT NULL REFERENCES {SCHEMA}.household(id),
  kind text NOT NULL CHECK (kind IN ('asset','liability','equity','income','expense')),
  source_account_id uuid,
  source_category_id uuid,
  currency char(3) NOT NULL CHECK (currency = 'ARS'),
  UNIQUE (household_id, id),
  FOREIGN KEY (household_id,source_account_id) REFERENCES {SCHEMA}.source_account(household_id,id),
  FOREIGN KEY (household_id,source_category_id) REFERENCES {SCHEMA}.source_category(household_id,id)
);
CREATE TABLE IF NOT EXISTS {SCHEMA}.journal_entry (
  id uuid PRIMARY KEY,
  household_id uuid NOT NULL REFERENCES {SCHEMA}.household(id),
  source_operation_id uuid NOT NULL,
  source_revision integer NOT NULL CHECK (source_revision > 0),
  purpose text NOT NULL CHECK (purpose IN ('effect','reversal')),
  source_audit_event_id uuid NOT NULL,
  effective_date date NOT NULL,
  recorded_at timestamptz NOT NULL,
  currency char(3) NOT NULL CHECK (currency = 'ARS'),
  operation_type text NOT NULL,
  category_id uuid,
  posted boolean NOT NULL DEFAULT false,
  UNIQUE (source_operation_id, source_revision, purpose, source_audit_event_id),
  UNIQUE (household_id, id),
  FOREIGN KEY (household_id,source_operation_id) REFERENCES {SCHEMA}.source_operation(household_id,id),
  FOREIGN KEY (household_id,source_audit_event_id) REFERENCES {SCHEMA}.source_audit_event(household_id,id),
  FOREIGN KEY (household_id,category_id) REFERENCES {SCHEMA}.source_category(household_id,id)
);
CREATE TABLE IF NOT EXISTS {SCHEMA}.posting (
  id bigserial PRIMARY KEY,
  household_id uuid NOT NULL,
  entry_id uuid NOT NULL,
  ledger_account_id uuid NOT NULL,
  line_no smallint NOT NULL,
  debit numeric(18,2) NOT NULL DEFAULT 0 CHECK (debit >= 0),
  credit numeric(18,2) NOT NULL DEFAULT 0 CHECK (credit >= 0),
  currency char(3) NOT NULL CHECK (currency = 'ARS'),
  financial_account_id uuid,
  category_id uuid,
  operation_type text NOT NULL,
  effective_date date NOT NULL,
  UNIQUE(entry_id, line_no),
  FOREIGN KEY (household_id, entry_id) REFERENCES {SCHEMA}.journal_entry(household_id, id),
  FOREIGN KEY (household_id, ledger_account_id) REFERENCES {SCHEMA}.ledger_account(household_id, id),
  FOREIGN KEY (household_id, financial_account_id) REFERENCES {SCHEMA}.source_account(household_id,id),
  FOREIGN KEY (household_id, category_id) REFERENCES {SCHEMA}.source_category(household_id,id),
  CHECK ((debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0))
);
CREATE INDEX IF NOT EXISTS poc_posting_house_date ON {SCHEMA}.posting(household_id, effective_date);
CREATE OR REPLACE FUNCTION {SCHEMA}.check_entry_balance() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE target uuid; n integer; d numeric; c numeric; currencies integer;
BEGIN
  IF TG_TABLE_NAME='journal_entry' THEN
    target := COALESCE(NEW.id, OLD.id);
  ELSE
    target := COALESCE(NEW.entry_id, OLD.entry_id);
  END IF;
  IF EXISTS (SELECT 1 FROM {SCHEMA}.journal_entry WHERE id=target AND posted) THEN
    SELECT count(*), coalesce(sum(debit),0), coalesce(sum(credit),0), count(DISTINCT currency)
      INTO n,d,c,currencies FROM {SCHEMA}.posting WHERE entry_id=target;
    IF n < 2 OR d <> c OR currencies <> 1 THEN
      RAISE EXCEPTION 'POC_UNBALANCED_ENTRY' USING ERRCODE='23514';
    END IF;
  END IF;
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS poc_entry_balance ON {SCHEMA}.posting;
CREATE CONSTRAINT TRIGGER poc_entry_balance AFTER INSERT OR UPDATE OR DELETE ON {SCHEMA}.posting
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.check_entry_balance();
DROP TRIGGER IF EXISTS poc_header_balance ON {SCHEMA}.journal_entry;
CREATE CONSTRAINT TRIGGER poc_header_balance AFTER INSERT OR UPDATE ON {SCHEMA}.journal_entry
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.check_entry_balance();
CREATE OR REPLACE FUNCTION {SCHEMA}.poc_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_TABLE_NAME='journal_entry' THEN
    IF OLD.posted AND (TG_OP='DELETE' OR NEW IS DISTINCT FROM OLD) THEN
      RAISE EXCEPTION 'POC_IMMUTABLE_ENTRY' USING ERRCODE='23514';
    END IF;
  ELSIF TG_TABLE_NAME='posting' THEN
    IF TG_OP IN ('UPDATE','DELETE') AND EXISTS
      (SELECT 1 FROM {SCHEMA}.journal_entry WHERE id=OLD.entry_id AND posted) THEN
      RAISE EXCEPTION 'POC_IMMUTABLE_POSTING' USING ERRCODE='23514';
    END IF;
  END IF;
  RETURN COALESCE(NEW, OLD);
END $$;
DROP TRIGGER IF EXISTS poc_journal_immutable ON {SCHEMA}.journal_entry;
CREATE TRIGGER poc_journal_immutable BEFORE UPDATE OR DELETE ON {SCHEMA}.journal_entry
  FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.poc_immutable();
DROP TRIGGER IF EXISTS poc_posting_immutable ON {SCHEMA}.posting;
CREATE TRIGGER poc_posting_immutable BEFORE UPDATE OR DELETE ON {SCHEMA}.posting
  FOR EACH ROW EXECUTE FUNCTION {SCHEMA}.poc_immutable();
"""


def dec(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("INVALID_AMOUNT") from exc
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        raise ValueError("INVALID_AMOUNT")
    return amount.quantize(Decimal("0.01"))


def field(snapshot, name, default=None):
    if name in snapshot:
        return snapshot[name]
    return snapshot.get(f"{name}_id", default)


def as_date(value):
    return value if hasattr(value, "year") else datetime.fromisoformat(str(value)).date()


def as_time(value):
    if isinstance(value, datetime):
        result = value
    else:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return result if result.tzinfo else result.replace(tzinfo=UTC)


def stable_uuid(*parts):
    return uuid.uuid5(uuid.NAMESPACE_URL, ":".join(map(str, parts)))


def signed_deltas(snapshot):
    amount = dec(snapshot["amount"])
    kind = snapshot["type"]
    account = str(field(snapshot, "account"))
    if kind in {"opening", "income"}:
        return {account: amount}
    if kind == "expense":
        return {account: -amount}
    if kind == "transfer":
        dest = str(field(snapshot, "destination"))
        if account == dest:
            raise ValueError("SAME_TRANSFER_ACCOUNT")
        return {account: -amount, dest: amount}
    raise ValueError("UNKNOWN_OPERATION_TYPE")


def source_expected(snapshot):
    return signed_deltas(snapshot)


def audit_chain(operation):
    events = sorted(operation.get("audit_events", []), key=lambda e: (e["created_at"], e["id"]))
    if not events:
        raise ValueError("MISSING_AUDIT_CHAIN")
    revisions = []
    for event in events:
        after = event.get("after") or {}
        if not after:
            raise ValueError("MISSING_AFTER_SNAPSHOT")
        action = event["action"]
        revision = int(after.get("revision", 0))
        status = after.get("status", "posted")
        snap = {**after}
        if not all(key in snap for key in ("type", "amount", "effective_date")):
            raise ValueError("INCOMPLETE_FINANCIAL_SNAPSHOT")
        if not field(snap, "account"):
            raise ValueError("INCOMPLETE_FINANCIAL_SNAPSHOT")
        category = field(snap, "category")
        destination = field(snap, "destination")
        if snap["type"] in {"income", "expense"} and (category is None or destination is not None):
            raise ValueError("INVALID_OPERATION_SHAPE")
        if snap["type"] == "transfer" and (category is not None or destination is None):
            raise ValueError("INVALID_OPERATION_SHAPE")
        if snap["type"] == "opening" and (category is not None or destination is not None):
            raise ValueError("INVALID_OPERATION_SHAPE")
        if action.endswith("create"):
            if revisions or revision != 1:
                raise ValueError("INVALID_CREATE_REVISION")
            purpose = "create"
        elif action.endswith("update"):
            if not revisions or revision != revisions[-1]["revision"] + 1:
                raise ValueError("REVISION_GAP")
            before = event.get("before") or {}
            if not before or not snapshots_match(before, revisions[-1]["snapshot"]):
                raise ValueError("BEFORE_SNAPSHOT_MISMATCH")
            purpose = "update"
        elif action.endswith("void"):
            if not revisions or revision != revisions[-1]["revision"]:
                raise ValueError("INVALID_VOID_REVISION")
            if status != "voided" or not snapshots_match(
                event.get("before") or {}, revisions[-1]["snapshot"]
            ):
                raise ValueError("INVALID_VOID_SNAPSHOT")
            revisions.append(
                {
                    "revision": revision,
                    "snapshot": revisions[-1]["snapshot"],
                    "event": event,
                    "void": True,
                }
            )
            continue
        else:
            raise ValueError("UNKNOWN_AUDIT_ACTION")
        if status != "posted":
            raise ValueError("INVALID_POSTED_STATUS")
        if revisions and not snapshots_match(event.get("before") or {}, revisions[-1]["snapshot"]):
            raise ValueError("BEFORE_SNAPSHOT_MISMATCH")
        snap["status"] = status
        signed_deltas(snap)
        revisions.append(
            {
                "revision": revision,
                "snapshot": snap,
                "event": event,
                "void": False,
                "purpose": purpose,
            }
        )
    current = operation
    if int(current.get("revision", 0)) != revisions[-1]["revision"]:
        raise ValueError("CURRENT_REVISION_MISMATCH")
    final = revisions[-1]
    if current.get("status", "posted") != ("voided" if final.get("void") else "posted"):
        raise ValueError("CURRENT_STATUS_MISMATCH")
    final_snapshot = {**final["snapshot"], "status": "voided" if final.get("void") else "posted"}
    if not snapshots_match(current, final_snapshot):
        raise ValueError("CURRENT_SNAPSHOT_MISMATCH")
    return revisions


def snapshots_match(left, right):
    # Compare financial identity, deliberately excluding mutable labels and audit metadata.
    fields = ("type", "amount", "effective_date", "status")
    for name in fields:
        a, b = left.get(name), right.get(name)
        if name == "status" and a is None:
            a = "posted"
        if a is not None and b is not None:
            if name == "amount":
                if dec(a) != dec(b):
                    return False
            elif name == "effective_date":
                if str(a)[:10] != str(b)[:10]:
                    return False
            elif str(a) != str(b):
                return False
    for name in ("account", "destination", "category"):
        a, b = field(left, name), field(right, name)
        if a is not None and b is not None and str(a) != str(b):
            return False
    return True


def validate_source_entries(operation, revisions):
    expected = {r["revision"]: source_expected(r["snapshot"]) for r in revisions}
    grouped = defaultdict(lambda: defaultdict(Decimal))
    for row in operation.get("ledger_entries", []):
        if row.get("household_id") and str(row["household_id"]) != str(operation["household_id"]):
            raise ValueError("CROSS_HOUSEHOLD_LEDGER_ENTRY")
        rev = int(row["revision"])
        grouped[rev][str(row["account_id"])] += Decimal(str(row["amount"]))
    if set(grouped) != set(expected):
        raise ValueError("LEDGER_REVISION_SET_MISMATCH")
    for rev, delta in expected.items():
        if dict(grouped[rev]) != delta:
            raise ValueError("LEDGER_REVISION_DELTA_MISMATCH")


def posting_lines(snapshot, reversal=False):
    amount = dec(snapshot["amount"])
    kind = snapshot["type"]
    account = str(field(snapshot, "account"))
    category = field(snapshot, "category")

    def line(account_kind, source_account, debit=Decimal("0"), credit=Decimal("0"), cat=None):
        if reversal:
            debit, credit = credit, debit
        return {
            "kind": account_kind,
            "source_account_id": source_account,
            "source_category_id": cat,
            "debit": debit,
            "credit": credit,
            "financial_account_id": source_account if account_kind == "asset" else None,
            "category_id": str(cat) if cat else None,
            "operation_type": kind,
        }

    if kind == "opening":
        return [line("asset", account, debit=amount), line("equity", None, credit=amount)]
    if kind == "income":
        return [
            line("asset", account, debit=amount),
            line("income", None, credit=amount, cat=category),
        ]
    if kind == "expense":
        return [
            line("expense", None, debit=amount, cat=category),
            line("asset", account, credit=amount),
        ]
    if kind == "transfer":
        dest = str(field(snapshot, "destination"))
        return [line("asset", dest, debit=amount), line("asset", account, credit=amount)]
    raise ValueError("UNKNOWN_OPERATION_TYPE")


def normalize_snapshot(source):
    if not isinstance(source, dict) or not isinstance(source.get("households"), list):
        raise ValueError("INVALID_SNAPSHOT")
    for collection in ("accounts", "categories", "operations"):
        if not isinstance(source.get(collection), list):
            raise ValueError("INVALID_SNAPSHOT")
    return source


def transform(source):
    """Pure deterministic transform, validates every source operation and audit chain."""
    source = normalize_snapshot(source)
    accounts = {str(a["id"]): a for a in source["accounts"]}
    categories = {str(c["id"]): c for c in source["categories"]}
    households = {str(h["id"]) for h in source["households"]}
    source_operations = [
        {
            "id": str(op["id"]),
            "household_id": str(op["household_id"]),
            "current_revision": int(op["revision"]),
            "status": op.get("status", "posted"),
        }
        for op in source["operations"]
    ]
    source_audit_events = [
        {
            "id": str(event["id"]),
            "household_id": str(op["household_id"]),
            "operation_id": str(op["id"]),
            "actor_id": str(event["actor_id"]) if event.get("actor_id") else None,
            "action": event["action"],
            "before": {
                k: v
                for k, v in (event.get("before") or {}).items()
                if k
                in {
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
                }
            },
            "after": {
                k: v
                for k, v in (event.get("after") or {}).items()
                if k
                in {
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
                }
            },
            "recorded_at": as_time(event["created_at"]),
        }
        for op in source["operations"]
        for event in op.get("audit_events", [])
    ]
    entries, ledgers = [], {}
    exceptions = []
    failed_operations = set()
    account_ids = {}
    for account_id, account in sorted(accounts.items()):
        home = str(account["household_id"])
        if home not in households or account.get("currency", "ARS") != "ARS":
            exceptions.append("ACCOUNT_REFERENCE_OR_CURRENCY")
            continue
        account_ids[account_id] = stable_uuid("asset", home, account_id)
    for op in sorted(source["operations"], key=lambda o: str(o["id"])):
        try:
            op_id, home = str(op["id"]), str(op["household_id"])
            if home not in households:
                raise ValueError("UNKNOWN_HOUSEHOLD")
            if any(
                e.get("household_id") and str(e["household_id"]) != home
                for e in op.get("audit_events", [])
            ):
                raise ValueError("CROSS_HOUSEHOLD_AUDIT_EVENT")
            revisions = audit_chain(op)
            validate_source_entries(op, revisions)
            for revision_row in revisions:
                snap = revision_row["snapshot"]
                for account_key in ("account", "destination"):
                    ref = field(snap, account_key)
                    if ref is not None and (
                        str(ref) not in accounts or str(accounts[str(ref)]["household_id"]) != home
                    ):
                        raise ValueError("CROSS_HOUSEHOLD_ACCOUNT")
                cat = field(snap, "category")
                if cat is not None and (
                    str(cat) not in categories or str(categories[str(cat)]["household_id"]) != home
                ):
                    raise ValueError("CROSS_HOUSEHOLD_CATEGORY")
                if cat is not None and categories[str(cat)]["type"] != snap["type"]:
                    raise ValueError("CATEGORY_TYPE_MISMATCH")
            for row in revisions:
                snap, rev, event = row["snapshot"], row["revision"], row["event"]
                if rev > 1 and not row.get("void"):
                    prior = revisions[revisions.index(row) - 1]
                    reverse_id = stable_uuid("journal", op_id, rev, "reversal")
                    reverse_date = as_date(prior["snapshot"]["effective_date"])
                    entries.append(
                        {
                            "id": reverse_id,
                            "household_id": home,
                            "source_operation_id": op_id,
                            "source_revision": rev,
                            "purpose": "reversal",
                            "source_audit_event_id": str(event["id"]),
                            "effective_date": reverse_date,
                            "recorded_at": as_time(event["created_at"]),
                            "currency": "ARS",
                            "operation_type": prior["snapshot"]["type"],
                            "category_id": field(prior["snapshot"], "category"),
                            "lines": posting_lines(prior["snapshot"], reversal=True),
                        }
                    )
                if row.get("void"):
                    prior = revisions[revisions.index(row) - 1]
                    entries.append(
                        {
                            "id": stable_uuid("journal", op_id, rev, "void"),
                            "household_id": home,
                            "source_operation_id": op_id,
                            "source_revision": rev,
                            "purpose": "reversal",
                            "source_audit_event_id": str(event["id"]),
                            "effective_date": as_date(prior["snapshot"]["effective_date"]),
                            "recorded_at": as_time(event["created_at"]),
                            "currency": "ARS",
                            "operation_type": prior["snapshot"]["type"],
                            "category_id": field(prior["snapshot"], "category"),
                            "lines": posting_lines(prior["snapshot"], reversal=True),
                        }
                    )
                    continue
                entries.append(
                    {
                        "id": stable_uuid("journal", op_id, rev, "effect"),
                        "household_id": home,
                        "source_operation_id": op_id,
                        "source_revision": rev,
                        "purpose": "effect",
                        "source_audit_event_id": str(event["id"]),
                        "effective_date": as_date(snap["effective_date"]),
                        "recorded_at": as_time(event["created_at"]),
                        "currency": "ARS",
                        "operation_type": snap["type"],
                        "category_id": field(snap, "category"),
                        "lines": posting_lines(snap),
                    }
                )
        except (ValueError, KeyError, TypeError) as exc:
            failed_operations.add(str(op.get("id", "unknown")))
            exceptions.append(str(exc) if str(exc).isupper() else "INVALID_OPERATION_HISTORY")
    for entry in entries:
        for line in entry["lines"]:
            src = line["source_account_id"]
            home = entry["household_id"]
            if src is not None:
                aid = str(src)
                if aid not in account_ids or str(accounts[aid]["household_id"]) != home:
                    exceptions.append("CROSS_HOUSEHOLD_POSTING")
                    failed_operations.add(str(entry["source_operation_id"]))
                    continue
                line["ledger_account_id"] = str(account_ids[aid])
            else:
                kind, cat = line["kind"], line["source_category_id"]
                line["ledger_account_id"] = str(stable_uuid("system", home, kind, cat or ""))
            line["household_id"] = home
        ledgers.update({entry["id"]: entry})
    if exceptions:
        return {
            "entries": [],
            "accounts": accounts,
            "categories": categories,
            "households": households,
            "source_operations": source_operations,
            "source_audit_events": source_audit_events,
            "failed_operation_count": len(failed_operations),
            "exceptions": sorted(exceptions),
        }
    return {
        "entries": entries,
        "accounts": accounts,
        "categories": categories,
        "households": households,
        "source_operations": source_operations,
        "source_audit_events": source_audit_events,
        "failed_operation_count": 0,
        "exceptions": [],
    }


def reset_schema(conn):
    with conn.transaction():
        conn.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
        conn.execute(DDL)


def load_target(conn, result, fail_after=None):
    """Transactional idempotent load; mismatch on a replay is fatal."""
    with conn.transaction():
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('gastio-ledger-migration-poc'))")
        conn.execute(DDL)
        for home in sorted(result["households"]):
            conn.execute(
                f"INSERT INTO {SCHEMA}.household(id) VALUES (%s) ON CONFLICT DO NOTHING", (home,)
            )
        for aid, account in sorted(result["accounts"].items()):
            cur = conn.execute(
                f"""INSERT INTO {SCHEMA}.source_account(id,household_id,currency,is_active)
                    VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (
                    aid,
                    account["household_id"],
                    account.get("currency", "ARS"),
                    account.get("is_active", True),
                ),
            )
            if cur.rowcount == 0:
                current = conn.execute(
                    f"SELECT household_id,currency,is_active FROM {SCHEMA}.source_account WHERE id=%s",
                    (aid,),
                ).fetchone()
                expected = (uuid.UUID(account["household_id"]), account.get("currency", "ARS"),
                            account.get("is_active", True))
                if current != expected:
                    raise ValueError("IDEMPOTENCY_SOURCE_ACCOUNT_MISMATCH")
        for cid, category in sorted(result["categories"].items()):
            cur = conn.execute(
                f"""INSERT INTO {SCHEMA}.source_category(id,household_id,operation_type,is_active)
                    VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (cid, category["household_id"], category["type"], category.get("is_active", True)),
            )
            if cur.rowcount == 0:
                current = conn.execute(
                    f"SELECT household_id,operation_type,is_active FROM {SCHEMA}.source_category WHERE id=%s",
                    (cid,),
                ).fetchone()
                expected = (uuid.UUID(category["household_id"]), category["type"],
                            category.get("is_active", True))
                if current != expected:
                    raise ValueError("IDEMPOTENCY_SOURCE_CATEGORY_MISMATCH")
        for op in result["source_operations"]:
            cur = conn.execute(
                f"""INSERT INTO {SCHEMA}.source_operation(id,household_id,current_revision,status)
                    VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (op["id"], op["household_id"], op["current_revision"], op["status"]),
            )
            if cur.rowcount == 0:
                current = conn.execute(
                    f"SELECT household_id,current_revision,status FROM {SCHEMA}.source_operation WHERE id=%s",
                    (op["id"],),
                ).fetchone()
                expected = (uuid.UUID(op["household_id"]), op["current_revision"], op["status"])
                if current != expected:
                    raise ValueError("IDEMPOTENCY_SOURCE_OPERATION_MISMATCH")
        for event in result["source_audit_events"]:
            cur = conn.execute(
                f"""INSERT INTO {SCHEMA}.source_audit_event
                    (id,household_id,operation_id,actor_id,action,before_snapshot,after_snapshot,recorded_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (
                    event["id"],
                    event["household_id"],
                    event["operation_id"],
                    event.get("actor_id"),
                    event["action"],
                    json.dumps(event["before"], default=str),
                    json.dumps(event["after"], default=str),
                    event["recorded_at"],
                ),
            )
            if cur.rowcount == 0:
                current = conn.execute(
                    f"""SELECT household_id,operation_id,actor_id,action,before_snapshot,after_snapshot,recorded_at
                        FROM {SCHEMA}.source_audit_event WHERE id=%s""",
                    (event["id"],),
                ).fetchone()
                expected = (uuid.UUID(event["household_id"]), uuid.UUID(event["operation_id"]),
                            uuid.UUID(event["actor_id"]) if event.get("actor_id") else None,
                            event["action"], event["before"], event["after"], event["recorded_at"])
                if current != expected:
                    raise ValueError("IDEMPOTENCY_SOURCE_AUDIT_MISMATCH")
        for aid, account in sorted(result["accounts"].items()):
            if aid not in {
                str(line["source_account_id"])
                for e in result["entries"]
                for line in e["lines"]
                if line["source_account_id"]
            }:
                continue
            ledger_id = str(stable_uuid("asset", account["household_id"], aid))
            conn.execute(
                f"INSERT INTO {SCHEMA}.ledger_account(id,household_id,kind,source_account_id,currency) VALUES (%s,%s,'asset',%s,'ARS') ON CONFLICT DO NOTHING",
                (ledger_id, account["household_id"], aid),
            )
        system_accounts = {}
        for entry in result["entries"]:
            for line in entry["lines"]:
                if line["source_account_id"] is None:
                    key = line["ledger_account_id"]
                    system_accounts[key] = (
                        entry["household_id"],
                        line["kind"],
                        line["source_category_id"],
                    )
        for ledger_id, (home, kind, cat) in sorted(system_accounts.items()):
            conn.execute(
                f"INSERT INTO {SCHEMA}.ledger_account(id,household_id,kind,source_category_id,currency) VALUES (%s,%s,%s,%s,'ARS') ON CONFLICT DO NOTHING",
                (ledger_id, home, kind, cat),
            )
        count = 0
        for entry in result["entries"]:
            cur = conn.execute(
                f"""INSERT INTO {SCHEMA}.journal_entry
                (id,household_id,source_operation_id,source_revision,purpose,source_audit_event_id,effective_date,recorded_at,currency,operation_type,category_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (
                    entry["id"],
                    entry["household_id"],
                    entry["source_operation_id"],
                    entry["source_revision"],
                    entry["purpose"],
                    entry["source_audit_event_id"],
                    entry["effective_date"],
                    entry["recorded_at"],
                    entry["currency"],
                    entry["operation_type"],
                    entry["category_id"],
                ),
            )
            if cur.rowcount == 0:
                current = conn.execute(
                    f"""SELECT household_id,source_operation_id,source_revision,purpose,
                        source_audit_event_id,effective_date,recorded_at,currency,operation_type,category_id
                        FROM {SCHEMA}.journal_entry WHERE id=%s""",
                    (entry["id"],),
                ).fetchone()
                expected = (
                    uuid.UUID(entry["household_id"]), uuid.UUID(entry["source_operation_id"]),
                    entry["source_revision"], entry["purpose"],
                    uuid.UUID(entry["source_audit_event_id"]), entry["effective_date"],
                    entry["recorded_at"], entry["currency"], entry["operation_type"],
                    uuid.UUID(entry["category_id"]) if entry["category_id"] else None,
                )
                if current != expected:
                    raise ValueError("IDEMPOTENCY_JOURNAL_MISMATCH")
            for ix, line in enumerate(entry["lines"], 1):
                cur = conn.execute(
                    f"""INSERT INTO {SCHEMA}.posting
                    (household_id,entry_id,ledger_account_id,line_no,debit,credit,currency,financial_account_id,category_id,operation_type,effective_date)
                    VALUES (%s,%s,%s,%s,%s,%s,'ARS',%s,%s,%s,%s) ON CONFLICT(entry_id,line_no) DO NOTHING""",
                    (
                        entry["household_id"],
                        entry["id"],
                        line["ledger_account_id"],
                        ix,
                        line["debit"],
                        line["credit"],
                        line["financial_account_id"],
                        line["category_id"],
                        line["operation_type"],
                        entry["effective_date"],
                    ),
                )
                if cur.rowcount == 0:
                    existing = conn.execute(
                        f"SELECT ledger_account_id,debit,credit,household_id FROM {SCHEMA}.posting WHERE entry_id=%s AND line_no=%s",
                        (entry["id"], ix),
                    ).fetchone()
                    if (
                        str(existing[0]),
                        Decimal(existing[1]),
                        Decimal(existing[2]),
                        str(existing[3]),
                    ) != (
                        str(line["ledger_account_id"]),
                        line["debit"],
                        line["credit"],
                        str(entry["household_id"]),
                    ):
                        raise ValueError("IDEMPOTENCY_CONTENT_MISMATCH")
            conn.execute(
                f"UPDATE {SCHEMA}.journal_entry SET posted=true WHERE id=%s AND NOT posted",
                (entry["id"],),
            )
            count += 1
            if fail_after is not None and count == fail_after:
                raise RuntimeError("SIMULATED_INTERRUPTION")


def reconcile(source, transformed, conn):
    """Independent SQL aggregation of target postings versus current source snapshots."""
    expected = defaultdict(Decimal)
    for op in source["operations"]:
        if op.get("status", "posted") != "posted":
            continue
        snap = {
            **op,
            "account": op.get("account_id"),
            "destination": op.get("destination_id"),
            "category": op.get("category_id"),
        }
        amount = dec(snap["amount"])
        month = str(snap["effective_date"])[:7]
        typ = snap["type"]
        if typ == "income":
            expected[("income", str(op["household_id"]), month, "")] += amount
        elif typ == "expense":
            expected[
                ("expense", str(op["household_id"]), month, str(op.get("category_id") or ""))
            ] += amount
        elif typ == "opening":
            expected[("opening", str(op["household_id"]), month, str(op["account_id"]))] += amount
        elif typ == "transfer":
            expected[("transfer", str(op["household_id"]), month, str(op["account_id"]))] += amount
        for account_id, delta in signed_deltas(snap).items():
            expected[("balance", str(op["household_id"]), account_id, "")] += delta
    actual_rows = conn.execute(
        f"""SELECT p.operation_type, p.household_id::text,
       to_char(p.effective_date,'YYYY-MM') AS period,
       coalesce(p.category_id::text,'') AS dimension,
       sum(CASE WHEN a.kind='income' THEN p.credit-p.debit
                ELSE p.debit-p.credit END) AS amount
       FROM {SCHEMA}.posting p
       JOIN {SCHEMA}.ledger_account a ON a.id=p.ledger_account_id
       WHERE a.kind IN ('income','expense')
       GROUP BY p.operation_type,p.household_id,p.effective_date,p.category_id"""
    ).fetchall()
    # Reconcile by deriving independent account balances and P&L from the journal.
    diffs = []
    target_balance = conn.execute(
        f"""SELECT p.household_id::text, la.source_account_id::text,
       sum(p.debit-p.credit) FROM {SCHEMA}.posting p JOIN {SCHEMA}.ledger_account la ON la.id=p.ledger_account_id
       WHERE la.kind='asset' GROUP BY p.household_id,la.source_account_id"""
    ).fetchall()
    target_bal = {("balance", h, a, ""): Decimal(v or 0) for h, a, v in target_balance}
    target_period = defaultdict(Decimal)
    for typ, home, period, cat, value in actual_rows:
        value = Decimal(value or 0)
        if typ == "income":
            target_period[("income", home, period, "")] += value
        elif typ == "expense":
            target_period[("expense", home, period, cat)] += value
        elif typ == "opening":
            # Openings are also identified from asset-side debit postings.
            pass
        elif typ == "transfer":
            pass
    for key, val in expected.items():
        if key[0] == "balance":
            actual = target_bal.get(key, Decimal(0))
        elif key[0] in {"income", "expense"}:
            actual = target_period.get(key, Decimal(0))
        elif key[0] == "opening":
            actual = conn.execute(
                f"SELECT coalesce(sum(debit),0) FROM {SCHEMA}.posting p JOIN {SCHEMA}.ledger_account a ON a.id=p.ledger_account_id WHERE p.household_id=%s AND p.operation_type='opening' AND a.source_account_id=%s AND p.debit>0",
                (key[1], key[3]),
            ).fetchone()[0]
        elif key[0] == "transfer":
            actual = conn.execute(
                f"SELECT coalesce(sum(credit),0) FROM {SCHEMA}.posting p JOIN {SCHEMA}.ledger_account a ON a.id=p.ledger_account_id WHERE p.household_id=%s AND p.operation_type='transfer' AND a.source_account_id=%s AND to_char(p.effective_date,'YYYY-MM')=%s",
                (key[1], key[3], key[2]),
            ).fetchone()[0]
        else:
            actual = Decimal(0)
        if Decimal(actual) != val:
            fingerprint = hashlib.sha256("|".join(key).encode()).hexdigest()[:12]
            diffs.append(
                {
                    "metric": key[0],
                    "dimension_hash": fingerprint,
                    "difference": str(Decimal(actual) - val),
                }
            )
    for key, val in target_period.items():
        if key not in expected and val:
            fingerprint = hashlib.sha256("|".join(key).encode()).hexdigest()[:12]
            diffs.append({"metric": key[0], "dimension_hash": fingerprint, "difference": str(val)})
    return diffs


def historical_source_metrics(source, cutoff):
    values = defaultdict(Decimal)
    for op in source["operations"]:
        states = audit_chain(op)
        available = [row for row in states if as_time(row["event"]["created_at"]) <= cutoff]
        if not available:
            continue
        current = available[-1]
        home = str(op["household_id"])
        if current.get("void"):
            values[("operation", home, "voided", current["snapshot"]["type"])] += 1
            continue
        snap = current["snapshot"]
        kind = snap["type"]
        month = str(snap["effective_date"])[:7]
        values[("operation", home, "posted", kind)] += 1
        for account_id, delta in signed_deltas(snap).items():
            values[("balance", home, account_id, "")] += delta
            if kind == "transfer":
                values[("transfer", home, account_id, month)] += delta
        amount = dec(snap["amount"])
        if kind == "income":
            values[("income", home, month, "")] += amount
        elif kind == "expense":
            values[("expense", home, month, str(field(snap, "category") or ""))] += amount
        elif kind == "opening":
            values[("opening", home, month, str(field(snap, "account")))] += amount
    return values


def reconcile_historical_cuts(source, conn):
    """Compare snapshots at each audit timestamp to journal state by recorded_at."""
    cutoffs = sorted(
        {as_time(event["created_at"]) for op in source["operations"]
         for event in op.get("audit_events", [])}
    )
    failures = []
    for cutoff in cutoffs:
        expected = historical_source_metrics(source, cutoff)
        actual = defaultdict(Decimal)
        rows = conn.execute(
            f"""SELECT p.operation_type,p.household_id::text,
                la.kind,la.source_account_id::text,p.category_id::text,
                to_char(p.effective_date,'YYYY-MM'),
                sum(p.debit-p.credit),sum(p.credit-p.debit)
                FROM {SCHEMA}.posting p
                JOIN {SCHEMA}.journal_entry j ON j.id=p.entry_id
                JOIN {SCHEMA}.ledger_account la ON la.id=p.ledger_account_id
                WHERE j.recorded_at <= %s
                GROUP BY p.operation_type,p.household_id,la.kind,la.source_account_id,
                         p.category_id,to_char(p.effective_date,'YYYY-MM')""",
            (cutoff,),
        ).fetchall()
        for kind, home, account_kind, account_id, category_id, month, debit_delta, credit_delta in rows:
            debit_delta, credit_delta = Decimal(debit_delta or 0), Decimal(credit_delta or 0)
            if account_kind == "asset" and account_id:
                actual[("balance", home, account_id, "")] += debit_delta
                if kind == "transfer":
                    actual[("transfer", home, account_id, month)] += debit_delta
                elif kind == "opening":
                    actual[("opening", home, month, account_id)] += debit_delta
            elif account_kind == "income":
                actual[("income", home, month, "")] += credit_delta
            elif account_kind == "expense":
                actual[("expense", home, month, category_id or "")] += debit_delta
        for op in source["operations"]:
            candidates = [e for e in op["audit_events"] if as_time(e["created_at"]) <= cutoff]
            if not candidates:
                continue
            final = candidates[-1]["after"]
            state = final.get("status", "posted")
            metric = ("operation", str(op["household_id"]), state, final.get("type", op["type"]))
            actual[metric] += 1
        keys = set(expected) | set(actual)
        for key in keys:
            if expected.get(key, Decimal(0)) != actual.get(key, Decimal(0)):
                cutoff_hash = hashlib.sha256(cutoff.isoformat().encode()).hexdigest()[:12]
                fp = hashlib.sha256(
                    "|".join(map(str, (cutoff_hash, *key))).encode()
                ).hexdigest()[:12]
                failures.append({"metric": key[0], "dimension_hash": fp,
                                 "cutoff_hash": cutoff_hash,
                                 "difference": str(actual.get(key, Decimal(0))-expected.get(key, Decimal(0)))})
    return cutoffs, failures


def run(snapshot_path, output_path, dsn, reset=False, fail_after=None):
    start = time.monotonic()
    report = {
        "executed_at": datetime.now(UTC).isoformat(),
        "tool_version": VERSION,
        "schema": SCHEMA,
        "source_schema": "gastio-phase1-financial-v1",
        "status": "INCOMPLETE",
        "households": 0,
        "accounts": 0,
        "operations": 0,
        "posted_operations": 0,
        "voided_operations": 0,
        "revisions": 0,
        "audit_events": 0,
        "receipts": 0,
        "journal_entries": 0,
        "postings": 0,
        "audit_events_copied": 0,
        "coverage_complete": False,
        "historical_cuts": 0,
        "historical_cut_differences": [],
        "omitted": 0,
        "errors": 0,
        "differences": [],
        "balanced": False,
        "reconciled": False,
    }
    try:
        source = json.loads(Path(snapshot_path).read_text())
        result = transform(source)
        report.update(
            {
                "households": len(result["households"]),
                "accounts": len(result["accounts"]),
                "operations": len(source["operations"]),
                "posted_operations": sum(
                    op.get("status", "posted") == "posted" for op in source["operations"]
                ),
                "voided_operations": sum(
                    op.get("status") == "voided" for op in source["operations"]
                ),
                "revisions": sum(
                    len({int(e.get("after", {}).get("revision", 0))
                         for e in o.get("audit_events", [])})
                    for o in source["operations"]
                ),
                "audit_events": sum(len(o.get("audit_events", [])) for o in source["operations"]),
                "receipts": int(source.get("receipt_count", 0)),
                "omitted": len(source["operations"]) if result["exceptions"] else 0,
                "errors": len(result["exceptions"]),
            }
        )
        if result["exceptions"]:
            report["error_codes"] = sorted(set(result["exceptions"]))
            report["status"] = "FAIL"
        else:
            if not dsn:
                raise ValueError("MISSING_POC_DSN")
            parsed = psycopg.conninfo.conninfo_to_dict(dsn)
            if not parsed.get("dbname", "").startswith(DB_PREFIX):
                raise ValueError("UNSAFE_TARGET_DATABASE")
            with psycopg.connect(dsn, autocommit=True) as conn:
                if reset:
                    reset_schema(conn)
                load_target(conn, result, fail_after=fail_after)
                report["journal_entries"] = conn.execute(
                    f"SELECT count(*) FROM {SCHEMA}.journal_entry"
                ).fetchone()[0]
                report["postings"] = conn.execute(
                    f"SELECT count(*) FROM {SCHEMA}.posting"
                ).fetchone()[0]
                report["audit_events_copied"] = conn.execute(
                    f"SELECT count(*) FROM {SCHEMA}.source_audit_event"
                ).fetchone()[0]
                expected_audits = sum(
                    len(op.get("audit_events", [])) for op in source["operations"]
                )
                source_op_count = conn.execute(
                    f"SELECT count(*) FROM {SCHEMA}.source_operation"
                ).fetchone()[0]
                source_status_counts = dict(
                    conn.execute(
                        f"SELECT status,count(*) FROM {SCHEMA}.source_operation GROUP BY status"
                    ).fetchall()
                )
                report["coverage_complete"] = (
                    source_op_count == len(source["operations"])
                    and source_status_counts.get("posted", 0) == report["posted_operations"]
                    and source_status_counts.get("voided", 0) == report["voided_operations"]
                    and report["audit_events_copied"] == expected_audits
                    and report["journal_entries"] == len(result["entries"])
                    and report["postings"]
                    == sum(len(entry["lines"]) for entry in result["entries"])
                )
                unbalanced = conn.execute(
                    f"""SELECT count(*) FROM (SELECT entry_id FROM {SCHEMA}.posting
                    GROUP BY entry_id HAVING count(*)<2 OR sum(debit)<>sum(credit) OR count(DISTINCT currency)<>1) q"""
                ).fetchone()[0]
                report["balanced"] = unbalanced == 0
                report["differences"] = reconcile(source, result, conn)
                cutoffs, report["historical_cut_differences"] = reconcile_historical_cuts(
                    source, conn
                )
                report["historical_cuts"] = len(cutoffs)
                report["reconciled"] = (
                    not report["differences"]
                    and not report["historical_cut_differences"]
                    and report["balanced"]
                    and report["coverage_complete"]
                )
                report["status"] = "PASS" if report["reconciled"] else "FAIL"
    except Exception as exc:  # report codes only; never leak DSN or source values
        code = (
            str(exc)
            if str(exc).isupper() and re.fullmatch(r"[A-Z0-9_]+", str(exc))
            else "PROCESSING_ERROR"
        )
        report["error_codes"] = sorted(set(report.get("error_codes", []) + [code]))
        report["errors"] = max(1, report["errors"])
        report["status"] = "INCOMPLETE" if code == "SIMULATED_INTERRUPTION" else "FAIL"
    report["duration_ms"] = round((time.monotonic() - start) * 1000, 2)
    Path(output_path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", required=True, help="Normalized JSON snapshot; never a database dump"
    )
    parser.add_argument("--report", required=True, help="Redacted JSON report output path")
    parser.add_argument(
        "--dsn-env", default="GASTIO_POC_DSN", help="Environment variable for isolated target DSN"
    )
    parser.add_argument(
        "--reset-poc-schema",
        action="store_true",
        help="Drop only migration_poc schema in guarded target DB",
    )
    parser.add_argument(
        "--simulate-interruption-after",
        type=int,
        help="Test-only failure after N journal entries; transaction must roll back",
    )
    args = parser.parse_args(argv)
    result = run(
        args.input,
        args.report,
        os.getenv(args.dsn_env),
        reset=args.reset_poc_schema,
        fail_after=args.simulate_interruption_after,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "report": args.report,
                "operations": result["operations"],
                "journal_entries": result["journal_entries"],
                "differences": len(result["differences"]),
                "error_codes": result.get("error_codes", []),
            }
        )
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
