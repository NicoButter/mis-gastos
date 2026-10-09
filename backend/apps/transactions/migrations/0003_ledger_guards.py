from django.db import migrations

SQL = """
CREATE FUNCTION gastio_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Financial history is immutable' USING ERRCODE='23514'; END $$;
CREATE TRIGGER ledger_immutable BEFORE UPDATE OR DELETE ON transactions_ledgerentry
FOR EACH ROW EXECUTE FUNCTION gastio_immutable();
CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_auditevent
FOR EACH ROW EXECUTE FUNCTION gastio_immutable();
CREATE TRIGGER receipt_immutable BEFORE UPDATE OR DELETE ON transactions_writereceipt
FOR EACH ROW EXECUTE FUNCTION gastio_immutable();
CREATE TRIGGER operation_no_delete BEFORE DELETE ON transactions_financialtransaction
FOR EACH ROW EXECUTE FUNCTION gastio_immutable();

CREATE FUNCTION gastio_operation_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE op transactions_financialtransaction%ROWTYPE;
DECLARE tid uuid; n integer; total numeric; source numeric; target numeric;
BEGIN
 IF TG_TABLE_NAME = 'transactions_ledgerentry' THEN tid := NEW.transaction_id;
 ELSE tid := NEW.id; END IF;
 SELECT * INTO op FROM transactions_financialtransaction WHERE id=tid;
 IF NOT EXISTS (SELECT 1 FROM wallets_financialaccount a
   WHERE a.id=op.account_id AND a.household_id=op.household_id AND a.currency=op.currency)
 OR (op.destination_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM wallets_financialaccount a
   WHERE a.id=op.destination_id AND a.household_id=op.household_id AND a.currency=op.currency))
 OR (op.category_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM categories_category c
   WHERE c.id=op.category_id AND c.household_id=op.household_id AND c.type=op.type))
 THEN RAISE EXCEPTION 'Cross-tenant or incompatible financial references' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM transactions_ledgerentry e JOIN wallets_financialaccount a ON a.id=e.account_id
   WHERE e.transaction_id=tid AND (e.household_id<>op.household_id
   OR a.household_id<>op.household_id OR a.currency<>op.currency OR e.revision>op.revision))
 THEN RAISE EXCEPTION 'Invalid ledger tenant or revision' USING ERRCODE='23514'; END IF;
 SELECT count(*), sum(amount), sum(amount) FILTER (WHERE account_id=op.account_id),
   sum(amount) FILTER (WHERE account_id=op.destination_id)
 INTO n,total,source,target FROM transactions_ledgerentry
 WHERE transaction_id=tid AND revision=op.revision;
 IF (op.type='transfer' AND (n<>2 OR total<>0 OR source IS DISTINCT FROM -op.amount
   OR target IS DISTINCT FROM op.amount))
 OR (op.type<>'transfer' AND (n<>1 OR source IS DISTINCT FROM
   CASE WHEN op.type='expense' THEN -op.amount ELSE op.amount END))
 THEN RAISE EXCEPTION 'Incomplete or inconsistent ledger operation' USING ERRCODE='23514'; END IF;
 IF NOT EXISTS (SELECT 1 FROM audit_auditevent e WHERE e.object_id=op.id
   AND e.household_id=op.household_id AND e.after->>'revision'=op.revision::text
   AND e.after->>'status'=op.status)
 THEN RAISE EXCEPTION 'Financial operation requires audit evidence' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER operation_consistent AFTER INSERT OR UPDATE ON transactions_financialtransaction
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION gastio_operation_guard();
CREATE CONSTRAINT TRIGGER ledger_consistent AFTER INSERT ON transactions_ledgerentry
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION gastio_operation_guard();

CREATE FUNCTION gastio_stable_fields() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.household_id<>OLD.household_id THEN
   RAISE EXCEPTION 'Tenant is immutable' USING ERRCODE='23514'; END IF;
 IF TG_TABLE_NAME='categories_category' THEN
   IF NEW.type<>OLD.type OR NEW.slug<>OLD.slug THEN
     RAISE EXCEPTION 'Category identity is immutable' USING ERRCODE='23514'; END IF;
 ELSIF NEW.currency<>OLD.currency THEN
   RAISE EXCEPTION 'Currency is immutable' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME='transactions_financialtransaction' THEN
   IF OLD.type='opening' OR OLD.status='voided' OR NEW.type<>OLD.type
     OR NEW.creator_id<>OLD.creator_id OR NEW.revision NOT IN (OLD.revision, OLD.revision+1)
     OR (NEW.status='posted' AND NEW.revision<>OLD.revision+1)
     OR (NEW.status='voided' AND (NEW.revision<>OLD.revision
       OR ROW(NEW.amount,NEW.account_id,NEW.destination_id,NEW.category_id,NEW.effective_date,NEW.description)
       IS DISTINCT FROM ROW(OLD.amount,OLD.account_id,OLD.destination_id,OLD.category_id,OLD.effective_date,OLD.description)))
   THEN RAISE EXCEPTION 'Invalid operation revision' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER account_stable BEFORE UPDATE ON wallets_financialaccount
FOR EACH ROW EXECUTE FUNCTION gastio_stable_fields();
CREATE TRIGGER category_stable BEFORE UPDATE ON categories_category
FOR EACH ROW EXECUTE FUNCTION gastio_stable_fields();
CREATE TRIGGER operation_stable BEFORE UPDATE ON transactions_financialtransaction
FOR EACH ROW EXECUTE FUNCTION gastio_stable_fields();
"""

REVERSE = """
DROP TRIGGER operation_stable ON transactions_financialtransaction;
DROP TRIGGER category_stable ON categories_category;
DROP TRIGGER account_stable ON wallets_financialaccount;
DROP FUNCTION gastio_stable_fields();
DROP TRIGGER ledger_consistent ON transactions_ledgerentry;
DROP TRIGGER operation_consistent ON transactions_financialtransaction;
DROP FUNCTION gastio_operation_guard();
DROP TRIGGER operation_no_delete ON transactions_financialtransaction;
DROP TRIGGER receipt_immutable ON transactions_writereceipt;
DROP TRIGGER audit_immutable ON audit_auditevent;
DROP TRIGGER ledger_immutable ON transactions_ledgerentry;
DROP FUNCTION gastio_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [("transactions", "0002_initial"), ("audit", "0001_initial")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
