from django.db import migrations
from django.utils.text import slugify


def seed(apps, schema_editor):
    Category = apps.get_model("categories", "Category")
    Household = apps.get_model("households", "Household")
    # Snapshot of defaults; migrations do not import mutable domain services.
    defaults = {
        "expense": [
            "Supermercado",
            "Alimentación",
            "Transporte",
            "Combustible",
            "Vivienda",
            "Servicios",
            "Salud",
            "Educación",
            "Mascotas",
            "Entretenimiento",
            "Impuestos",
            "Suscripciones",
            "Otros gastos",
        ],
        "income": ["Sueldo", "Trabajo independiente", "Ventas", "Reintegros", "Otros ingresos"],
    }
    for household_id in Household.objects.values_list("id", flat=True).iterator():
        for kind, names in defaults.items():
            for name in names:
                Category.objects.get_or_create(
                    household_id=household_id,
                    slug=f"{kind}-{slugify(name)}",
                    defaults={"name": name, "type": kind},
                )


class Migration(migrations.Migration):
    dependencies = [("categories", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
