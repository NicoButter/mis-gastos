from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, F, Prefetch, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from apps.categories.models import Category
from apps.transactions.models import FinancialTransaction
from apps.transactions.services import Conflict, audit, post_entries, scoped, snapshot
from apps.wallets.models import FinancialAccount

from .models import CardInstallment, CardPurchase, CreditCard, InstallmentPayment
from .serializers import CardOutput, InstallmentOutput, PurchaseOutput


def month_day(year, month, day, offset=0):
    index = year * 12 + month - 1 + offset
    year, month = index // 12, index % 12 + 1
    if year > 9999:
        raise ValidationError({"purchase_date": "Calendario fuera de rango."})
    return date(year, month, min(day, monthrange(year, month)[1]))


def schedule(amount, count, purchase_date, closing_day, due_day):
    amounts = split_amount(amount, count)
    closing = month_day(purchase_date.year, purchase_date.month, closing_day)
    offset = int(purchase_date > closing)
    result = []
    for index in range(count):
        closing = month_day(purchase_date.year, purchase_date.month, closing_day, offset + index)
        due = month_day(closing.year, closing.month, due_day)
        if due <= closing:
            due = month_day(closing.year, closing.month, due_day, 1)
        result.append((amounts[index], closing, due))
    return result


def installments(household_id):
    zero = Value(Decimal("0"), output_field=DecimalField(max_digits=24, decimal_places=2))
    return (
        CardInstallment.objects.filter(household_id=household_id)
        .select_related("purchase__card", "payment__account")
        .annotate(
            paid_amount=Coalesce(F("payment__amount"), zero)
            + Coalesce(Sum("payments__transaction__amount"), zero)
        )
        .annotate(pending_amount=F("amount") - F("paid_amount"))
        .order_by("due_date", "purchase_id", "number")
        .prefetch_related(
            Prefetch(
                "payments",
                queryset=InstallmentPayment.objects.select_related("transaction__account"),
            )
        )
    )


def purchases(household_id):
    return (
        CardPurchase.objects.filter(household_id=household_id)
        .select_related("card")
        .prefetch_related(Prefetch("installments", queryset=installments(household_id)))
    )


def split_amount(amount, count):
    base, remainder = divmod(int(amount * 100), count)
    if base == 0:
        raise ValidationError({"amount": "Cada cuota debe ser de al menos $0,01."})
    return [Decimal(base + (index < remainder)) / 100 for index in range(count)]


def mutate(membership, action, data, pk):
    if action == "card.create":
        obj = CreditCard.objects.create(household_id=membership.household_id, **data)
        audit(membership, action, obj)
        return CardOutput(obj).data
    if action == "card.update":
        obj = scoped(CreditCard, membership, pk)
        before = snapshot(obj)
        for field, value in data.items():
            setattr(obj, field, value)
        obj.save()
        audit(membership, action, obj, before)
        return CardOutput(obj).data
    if action == "card_purchase.create":
        data = dict(data)
        data.pop("frequency", None)
        card = scoped(CreditCard, membership, data["card_id"]) if data.get("card_id") else None
        category = scoped(Category, membership, data["category_id"])
        if (card and not card.is_active) or not category.is_active or category.type != "expense":
            raise ValidationError("Elegí una tarjeta y categoría de gasto activas.")
        if card:
            if data.get("first_due_date"):
                raise ValidationError({"first_due_date": "La tarjeta define sus vencimientos."})
            rows = schedule(
                data["amount"],
                data["installments_count"],
                data["purchase_date"],
                card.closing_day,
                card.due_day,
            )
        else:
            first = data.get("first_due_date")
            if not first:
                raise ValidationError({"first_due_date": "Elegí la fecha de la primera cuota."})
            rows = [
                (amount, None, month_day(first.year, first.month, first.day, index))
                for index, amount in enumerate(
                    split_amount(data["amount"], data["installments_count"])
                )
            ]
        obj = CardPurchase.objects.create(
            household_id=membership.household_id, creator=membership.user, **data
        )
        CardInstallment.objects.bulk_create(
            [
                CardInstallment(
                    household_id=membership.household_id,
                    purchase=obj,
                    number=index + 1,
                    amount=amount,
                    closing_date=closing,
                    due_date=due,
                )
                for index, (amount, closing, due) in enumerate(rows)
            ]
        )
        audit(membership, action, obj)
        return PurchaseOutput(purchases(membership.household_id).get(pk=obj.pk)).data
    obj = scoped(CardInstallment, membership, pk)
    obj = installments(membership.household_id).get(pk=obj.pk)
    if obj.pending_amount <= 0:
        raise Conflict("Esta cuota ya está pagada.")
    amount = data.get("amount", obj.pending_amount)
    if amount > obj.pending_amount:
        raise ValidationError({"amount": "El pago supera el importe pendiente."})
    if obj.purchase.card_id and amount != obj.amount:
        raise ValidationError({"amount": "Las cuotas de tarjeta se pagan completas."})
    account = scoped(FinancialAccount, membership, data["account_id"])
    if not account.is_active or account.currency != "ARS":
        raise ValidationError({"account_id": "Elegí una cuenta activa en ARS."})
    before = snapshot(obj)
    payment = FinancialTransaction.objects.create(
        household_id=membership.household_id,
        creator=membership.user,
        type="card_payment",
        amount=amount,
        account=account,
        effective_date=data["effective_date"],
        description=f"Pago cuota {obj.number} · {obj.purchase.description}"[:500],
    )
    post_entries(payment)
    audit(membership, "card_payment.create", payment)
    if obj.purchase.card_id:
        obj.payment = payment
        obj.save(update_fields=["payment"])
    else:
        record = InstallmentPayment.objects.create(
            household_id=membership.household_id, installment=obj, transaction=payment
        )
        audit(membership, "installment_payment.create", record)
    audit(membership, action, obj, before)
    return InstallmentOutput(installments(membership.household_id).get(pk=obj.pk)).data
