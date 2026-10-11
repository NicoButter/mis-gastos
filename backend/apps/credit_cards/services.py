from calendar import monthrange
from datetime import date
from decimal import Decimal

from rest_framework.exceptions import ValidationError

from apps.categories.models import Category
from apps.transactions.models import FinancialTransaction
from apps.transactions.services import Conflict, audit, post_entries, scoped, snapshot
from apps.wallets.models import FinancialAccount

from .models import CardInstallment, CardPurchase, CreditCard
from .serializers import CardOutput, InstallmentOutput, PurchaseOutput


def month_day(year, month, day, offset=0):
    index = year * 12 + month - 1 + offset
    year, month = index // 12, index % 12 + 1
    if year > 9999:
        raise ValidationError({"purchase_date": "Calendario fuera de rango."})
    return date(year, month, min(day, monthrange(year, month)[1]))


def schedule(amount, count, purchase_date, closing_day, due_day):
    cents = int(amount * 100)
    base, remainder = divmod(cents, count)
    if base == 0:
        raise ValidationError({"amount": "Cada cuota debe ser de al menos $0,01."})
    closing = month_day(purchase_date.year, purchase_date.month, closing_day)
    offset = int(purchase_date > closing)
    result = []
    for index in range(count):
        closing = month_day(purchase_date.year, purchase_date.month, closing_day, offset + index)
        due = month_day(closing.year, closing.month, due_day)
        if due <= closing:
            due = month_day(closing.year, closing.month, due_day, 1)
        result.append((Decimal(base + (index < remainder)) / 100, closing, due))
    return result


def installments(household_id):
    return CardInstallment.objects.filter(household_id=household_id).select_related(
        "purchase__card", "payment__account"
    )


def purchases(household_id):
    return (
        CardPurchase.objects.filter(household_id=household_id)
        .select_related("card")
        .prefetch_related("installments__purchase__card", "installments__payment__account")
    )


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
        card = scoped(CreditCard, membership, data["card_id"])
        category = scoped(Category, membership, data["category_id"])
        if not card.is_active or not category.is_active or category.type != "expense":
            raise ValidationError("Elegí una tarjeta activa y una categoría de gasto activa.")
        rows = schedule(
            data["amount"],
            data["installments_count"],
            data["purchase_date"],
            card.closing_day,
            card.due_day,
        )
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
    if obj.payment_id:
        raise Conflict("Esta cuota ya está pagada.")
    account = scoped(FinancialAccount, membership, data["account_id"])
    if not account.is_active or account.currency != "ARS":
        raise ValidationError({"account_id": "Elegí una cuenta activa en ARS."})
    before = snapshot(obj)
    payment = FinancialTransaction.objects.create(
        household_id=membership.household_id,
        creator=membership.user,
        type="card_payment",
        amount=obj.amount,
        account=account,
        effective_date=data["effective_date"],
        description=f"Pago tarjeta · cuota {obj.number} · {obj.purchase.description}"[:500],
    )
    post_entries(payment)
    audit(membership, "card_payment.create", payment)
    obj.payment = payment
    obj.save(update_fields=["payment"])
    audit(membership, action, obj, before)
    return InstallmentOutput(installments(membership.household_id).get(pk=obj.pk)).data
