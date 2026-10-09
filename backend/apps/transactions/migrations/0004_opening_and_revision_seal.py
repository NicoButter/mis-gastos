from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("transactions", "0003_ledger_guards")]
    operations = [
        migrations.AddConstraint(
            model_name="financialtransaction",
            constraint=models.UniqueConstraint(
                fields=["account"],
                condition=models.Q(type="opening"),
                name="single_account_opening",
            ),
        ),
        migrations.RunSQL(
            """
            CREATE FUNCTION gastio_current_revision_only() RETURNS trigger LANGUAGE plpgsql AS $$
            DECLARE current_revision integer; current_status varchar;
            BEGIN
              SELECT revision,status INTO current_revision,current_status
              FROM transactions_financialtransaction WHERE id=NEW.transaction_id;
              IF NEW.revision<>current_revision OR current_status<>'posted' THEN
                RAISE EXCEPTION 'Cannot append to historical or voided ledger revisions'
                USING ERRCODE='23514';
              END IF;
              RETURN NEW;
            END $$;
            CREATE TRIGGER ledger_current_revision BEFORE INSERT ON transactions_ledgerentry
            FOR EACH ROW EXECUTE FUNCTION gastio_current_revision_only();
            """,
            "DROP TRIGGER ledger_current_revision ON transactions_ledgerentry; "
            "DROP FUNCTION gastio_current_revision_only();",
        ),
    ]
