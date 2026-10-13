from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="terms_accepted_version",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="user",
            name="terms_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
