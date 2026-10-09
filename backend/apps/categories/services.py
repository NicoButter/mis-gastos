from django.db import transaction
from django.utils.text import slugify

from apps.households.models import Household

from .models import Category

DEFAULTS = {
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


@transaction.atomic
def seed_categories(household_id):
    """Explicit, serialized, idempotent seed; never creates financial data."""
    Household.objects.select_for_update().get(pk=household_id)
    for kind, names in DEFAULTS.items():
        for name in names:
            Category.objects.get_or_create(
                household_id=household_id,
                slug=f"{kind}-{slugify(name)}",
                defaults={"name": name, "type": kind},
            )
