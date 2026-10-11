from django.db import migrations

SQL = """
CREATE FUNCTION gastio_card_guard() RETURNS trigger LANGUAGE plpgsql AS $$
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
CREATE TRIGGER card_guard BEFORE UPDATE ON credit_cards_creditcard
FOR EACH ROW EXECUTE FUNCTION gastio_card_guard();
CREATE TRIGGER card_purchase_guard BEFORE INSERT OR UPDATE ON credit_cards_cardpurchase
FOR EACH ROW EXECUTE FUNCTION gastio_card_guard();
CREATE TRIGGER card_installment_guard BEFORE INSERT OR UPDATE ON credit_cards_cardinstallment
FOR EACH ROW EXECUTE FUNCTION gastio_card_guard();
CREATE TRIGGER card_purchase_no_delete BEFORE DELETE ON credit_cards_cardpurchase
FOR EACH ROW EXECUTE FUNCTION gastio_immutable();
CREATE TRIGGER card_installment_no_delete BEFORE DELETE ON credit_cards_cardinstallment
FOR EACH ROW EXECUTE FUNCTION gastio_immutable();
"""
REVERSE = """
DROP TRIGGER card_installment_no_delete ON credit_cards_cardinstallment;
DROP TRIGGER card_purchase_no_delete ON credit_cards_cardpurchase;
DROP TRIGGER card_installment_guard ON credit_cards_cardinstallment;
DROP TRIGGER card_purchase_guard ON credit_cards_cardpurchase;
DROP TRIGGER card_guard ON credit_cards_creditcard;
DROP FUNCTION gastio_card_guard();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("credit_cards", "0001_initial"),
        ("transactions", "0006_card_payment_guards"),
    ]
    operations = [migrations.RunSQL(SQL, REVERSE)]
