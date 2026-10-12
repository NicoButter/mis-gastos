from django.db import migrations

SQL = """
CREATE FUNCTION gastio_recurring_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_TABLE_NAME='recurring_recurringexpense' THEN
   IF NOT EXISTS (SELECT 1 FROM categories_category c WHERE c.id=NEW.category_id
      AND c.household_id=NEW.household_id AND c.type='expense')
   OR (NEW.account_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM wallets_financialaccount a
      WHERE a.id=NEW.account_id AND a.household_id=NEW.household_id)) THEN
     RAISE EXCEPTION 'Invalid recurring references' USING ERRCODE='23514'; END IF;
   IF TG_OP='UPDATE' AND ROW(NEW.household_id,NEW.creator_id,NEW.name,NEW.category_id,NEW.amount,NEW.start_date,NEW.due_day,NEW.account_id)
     IS DISTINCT FROM ROW(OLD.household_id,OLD.creator_id,OLD.name,OLD.category_id,OLD.amount,OLD.start_date,OLD.due_day,OLD.account_id) THEN
     RAISE EXCEPTION 'Recurring identity is immutable' USING ERRCODE='23514'; END IF;
 ELSE
   IF NOT EXISTS (SELECT 1 FROM recurring_recurringexpense r WHERE r.id=NEW.recurring_id
      AND r.household_id=NEW.household_id) THEN
     RAISE EXCEPTION 'Invalid occurrence tenant' USING ERRCODE='23514'; END IF;
   IF NEW.payment_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM transactions_financialtransaction t JOIN recurring_recurringexpense r ON r.id=NEW.recurring_id
      WHERE t.id=NEW.payment_id AND t.household_id=NEW.household_id AND t.type='expense'
      AND t.amount=NEW.amount AND t.category_id=r.category_id AND t.status='posted') THEN
     RAISE EXCEPTION 'Invalid recurring payment' USING ERRCODE='23514'; END IF;
   IF TG_OP='UPDATE' AND ((OLD.status<>'pending' AND NOT (OLD.status='cancelled' AND NEW.status='pending'
      AND EXISTS (SELECT 1 FROM recurring_recurringexpense WHERE id=NEW.recurring_id AND status='active'))) OR ROW(NEW.household_id,NEW.recurring_id,NEW.due_date)
      IS DISTINCT FROM ROW(OLD.household_id,OLD.recurring_id,OLD.due_date)) THEN
     RAISE EXCEPTION 'Occurrence history is immutable' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER recurring_guard BEFORE INSERT OR UPDATE ON recurring_recurringexpense
FOR EACH ROW EXECUTE FUNCTION gastio_recurring_guard();
CREATE TRIGGER occurrence_guard BEFORE INSERT OR UPDATE ON recurring_recurringoccurrence
FOR EACH ROW EXECUTE FUNCTION gastio_recurring_guard();
CREATE TRIGGER occurrence_no_delete BEFORE DELETE ON recurring_recurringoccurrence
FOR EACH ROW EXECUTE FUNCTION gastio_immutable();
CREATE TRIGGER recurring_no_delete BEFORE DELETE ON recurring_recurringexpense
FOR EACH ROW EXECUTE FUNCTION gastio_immutable();
CREATE FUNCTION gastio_recurring_payment_stable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS (SELECT 1 FROM recurring_recurringoccurrence WHERE payment_id=OLD.id) THEN
   RAISE EXCEPTION 'Recurring payment is immutable' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER recurring_payment_stable BEFORE UPDATE ON transactions_financialtransaction
FOR EACH ROW EXECUTE FUNCTION gastio_recurring_payment_stable();
"""
REVERSE = """
DROP TRIGGER recurring_payment_stable ON transactions_financialtransaction;
DROP FUNCTION gastio_recurring_payment_stable();
DROP TRIGGER recurring_no_delete ON recurring_recurringexpense;
DROP TRIGGER occurrence_no_delete ON recurring_recurringoccurrence;
DROP TRIGGER occurrence_guard ON recurring_recurringoccurrence;
DROP TRIGGER recurring_guard ON recurring_recurringexpense;
DROP FUNCTION gastio_recurring_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("recurring", "0001_initial")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
