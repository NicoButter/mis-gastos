from django.db import migrations

SQL = """
CREATE OR REPLACE FUNCTION gastio_card_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_TABLE_NAME='credit_cards_creditcard' THEN
   IF TG_OP='UPDATE' AND NEW.household_id<>OLD.household_id THEN
     RAISE EXCEPTION 'Card tenant is immutable' USING ERRCODE='23514';
   END IF;
 ELSIF TG_TABLE_NAME='credit_cards_cardpurchase' THEN
   IF (NEW.card_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM credit_cards_creditcard c WHERE c.id=NEW.card_id
      AND c.household_id=NEW.household_id))
   OR NOT EXISTS (SELECT 1 FROM categories_category c WHERE c.id=NEW.category_id
      AND c.household_id=NEW.household_id AND c.type='expense') THEN
     RAISE EXCEPTION 'Invalid purchase tenant' USING ERRCODE='23514';
   END IF;
   IF TG_OP='UPDATE' THEN
     RAISE EXCEPTION 'Purchase is immutable' USING ERRCODE='23514';
   END IF;
 ELSE
   IF NOT EXISTS (SELECT 1 FROM credit_cards_cardpurchase p WHERE p.id=NEW.purchase_id
      AND p.household_id=NEW.household_id AND NEW.number<=p.installments_count)
   OR (NEW.closing_date IS NOT NULL AND NEW.due_date<=NEW.closing_date) THEN
     RAISE EXCEPTION 'Invalid installment' USING ERRCODE='23514';
   END IF;
   IF NEW.payment_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM transactions_financialtransaction t WHERE t.id=NEW.payment_id
      AND t.household_id=NEW.household_id AND t.type='card_payment'
      AND t.amount=NEW.amount AND t.status='posted') THEN
     RAISE EXCEPTION 'Invalid installment payment' USING ERRCODE='23514';
   END IF;
   IF TG_OP='UPDATE' AND (OLD.payment_id IS NOT NULL
     OR ROW(NEW.household_id,NEW.purchase_id,NEW.number,NEW.amount,NEW.closing_date,NEW.due_date)
     IS DISTINCT FROM ROW(OLD.household_id,OLD.purchase_id,OLD.number,OLD.amount,OLD.closing_date,OLD.due_date)) THEN
     RAISE EXCEPTION 'Installment is immutable except first payment' USING ERRCODE='23514';
   END IF;
 END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION gastio_installment_payment_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE total numeric; i credit_cards_cardinstallment%ROWTYPE;
BEGIN
 SELECT * INTO i FROM credit_cards_cardinstallment WHERE id=NEW.installment_id;
 IF NEW.household_id<>i.household_id
 OR NOT EXISTS (SELECT 1 FROM credit_cards_cardpurchase p WHERE p.id=i.purchase_id AND p.card_id IS NULL)
 OR NOT EXISTS (SELECT 1 FROM transactions_financialtransaction t WHERE t.id=NEW.transaction_id
   AND t.household_id=i.household_id AND t.type='card_payment' AND t.status='posted') THEN
   RAISE EXCEPTION 'Invalid installment payment references' USING ERRCODE='23514'; END IF;
 SELECT sum(t.amount) INTO total FROM credit_cards_installmentpayment p
 JOIN transactions_financialtransaction t ON t.id=p.transaction_id WHERE p.installment_id=i.id;
 IF total>i.amount THEN RAISE EXCEPTION 'Installment overpayment' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER installment_payment_guard AFTER INSERT ON credit_cards_installmentpayment
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION gastio_installment_payment_guard();
CREATE TRIGGER installment_payment_immutable BEFORE UPDATE OR DELETE ON credit_cards_installmentpayment
FOR EACH ROW EXECUTE FUNCTION gastio_immutable();
"""
REVERSE = """
DROP TRIGGER installment_payment_immutable ON credit_cards_installmentpayment;
DROP TRIGGER installment_payment_guard ON credit_cards_installmentpayment;
DROP FUNCTION gastio_installment_payment_guard();
CREATE OR REPLACE FUNCTION gastio_card_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_TABLE_NAME='credit_cards_creditcard' THEN
   IF TG_OP='UPDATE' AND NEW.household_id<>OLD.household_id THEN
     RAISE EXCEPTION 'Card tenant is immutable' USING ERRCODE='23514';
   END IF;
 ELSIF TG_TABLE_NAME='credit_cards_cardpurchase' THEN
   IF NOT EXISTS (SELECT 1 FROM credit_cards_creditcard c WHERE c.id=NEW.card_id
      AND c.household_id=NEW.household_id)
   OR NOT EXISTS (SELECT 1 FROM categories_category c WHERE c.id=NEW.category_id
      AND c.household_id=NEW.household_id AND c.type='expense') THEN
     RAISE EXCEPTION 'Invalid purchase tenant' USING ERRCODE='23514';
   END IF;
   IF TG_OP='UPDATE' THEN
     RAISE EXCEPTION 'Purchase is immutable' USING ERRCODE='23514';
   END IF;
 ELSE
   IF NOT EXISTS (SELECT 1 FROM credit_cards_cardpurchase p WHERE p.id=NEW.purchase_id
      AND p.household_id=NEW.household_id AND NEW.number<=p.installments_count)
   OR NEW.due_date<=NEW.closing_date THEN
     RAISE EXCEPTION 'Invalid installment' USING ERRCODE='23514';
   END IF;
   IF NEW.payment_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM transactions_financialtransaction t WHERE t.id=NEW.payment_id
      AND t.household_id=NEW.household_id AND t.type='card_payment'
      AND t.amount=NEW.amount AND t.status='posted') THEN
     RAISE EXCEPTION 'Invalid installment payment' USING ERRCODE='23514';
   END IF;
   IF TG_OP='UPDATE' AND (OLD.payment_id IS NOT NULL
     OR ROW(NEW.household_id,NEW.purchase_id,NEW.number,NEW.amount,NEW.closing_date,NEW.due_date)
     IS DISTINCT FROM ROW(OLD.household_id,OLD.purchase_id,OLD.number,OLD.amount,OLD.closing_date,OLD.due_date)) THEN
     RAISE EXCEPTION 'Installment is immutable except first payment' USING ERRCODE='23514';
   END IF;
 END IF;
 RETURN NEW;
END $$;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("credit_cards", "0003_cardpurchase_creditor_cardpurchase_first_due_date_and_more")
    ]
    operations = [migrations.RunSQL(SQL, REVERSE)]
