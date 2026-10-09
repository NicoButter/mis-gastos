import uuid

from django.db import models


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=[("income", "Ingreso"), ("expense", "Gasto")])
    slug = models.SlugField(max_length=120)
    is_active = models.BooleanField(default=True)
    color = models.CharField(max_length=7, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["type", "name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["household", "slug"], name="category_household_slug"),
            models.CheckConstraint(
                condition=models.Q(type__in=["income", "expense"]), name="category_valid_type"
            ),
        ]
