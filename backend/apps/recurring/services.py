from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.categories.models import Category
from apps.credit_cards.services import month_day
from apps.households.models import Household
from apps.households.services import resolve_active_membership
from apps.transactions.models import FinancialTransaction
from apps.transactions.services import Conflict, audit, authorize, post_entries, scoped, snapshot
from apps.wallets.models import FinancialAccount

from .models import RecurringExpense, RecurringOccurrence
from .serializers import OccurrenceOutput, RecurringOutput


def occurrences(household_id):
    return RecurringOccurrence.objects.filter(household_id=household_id).select_related(
        "recurring", "payment__account"
    )


def rules(household_id):
    return RecurringExpense.objects.filter(household_id=household_id).prefetch_related(
        Prefetch("occurrences", queryset=occurrences(household_id))
    )


def generate(membership, rule):
    if rule.status != "active":
        return
    today = timezone.localdate()
    first = month_day(rule.start_date.year, rule.start_date.month, rule.due_day)
    if first < rule.start_date:
        first = month_day(first.year, first.month, rule.due_day, 1)
    horizon = max(first, month_day(today.year, today.month, 31, 2))
    count = (horizon.year - first.year) * 12 + horizon.month - first.month + 1
    if count > 1200:
        raise ValidationError({"start_date": "La fecha de inicio excede 100 años de ocurrencias."})
    existing = set(rule.occurrences.values_list("due_date", flat=True))
    for index in range(count):
        due = month_day(first.year, first.month, rule.due_day, index)
        if due not in existing:
            if rule.resume_date and due < rule.resume_date:
                continue
            obj = RecurringOccurrence.objects.create(
                household_id=membership.household_id,
                recurring=rule,
                amount=rule.amount,
                due_date=due,
            )
            audit(membership, "recurring_occurrence.create", obj)


@transaction.atomic
def ensure_occurrences(user, household_id):
    Household.objects.select_for_update().get(pk=household_id)
    membership = resolve_active_membership(user, household_id)
    authorize(membership)
    for rule in RecurringExpense.objects.filter(household_id=household_id, status="active"):
        generate(membership, rule)


def payment_account(membership, pk):
    if not pk:
        raise ValidationError({"account_id": "Seleccioná una cuenta de pago."})
    account = scoped(FinancialAccount, membership, pk)
    if not account.is_active:
        raise ValidationError({"account_id": "La cuenta está archivada."})
    return account


def mutate(membership, action, data, pk):
    if action == "recurring.create":
        data = dict(data)
        data.pop("frequency", None)
        category = scoped(Category, membership, data["category_id"])
        if not category.is_active or category.type != "expense":
            raise ValidationError({"category_id": "Elegí una categoría de gasto activa."})
        if data.get("account_id"):
            payment_account(membership, data["account_id"])
        obj = RecurringExpense.objects.create(
            household_id=membership.household_id, creator=membership.user, **data
        )
        audit(membership, action, obj)
        generate(membership, obj)
        return RecurringOutput(
            rules(membership.household_id).get(pk=obj.pk), context={"membership": membership}
        ).data
    if action == "recurring.update":
        obj = scoped(RecurringExpense, membership, pk)
        if membership.role == "member" and obj.creator_id != membership.user_id:
            raise PermissionDenied("Sólo podés modificar tus propias recurrencias.")
        if obj.status == "cancelled":
            raise Conflict("La recurrencia está cancelada.")
        before = snapshot(obj)
        obj.status = data["status"]
        if obj.status == "active" and before["status"] == "paused":
            obj.resume_date = timezone.localdate()
        obj.save(update_fields=["status", "resume_date"])
        audit(membership, action, obj, before)
        if obj.status != "active":
            for occurrence in obj.occurrences.filter(
                status="pending", due_date__gte=timezone.localdate()
            ):
                previous = snapshot(occurrence)
                occurrence.status = "cancelled"
                occurrence.save(update_fields=["status"])
                audit(membership, "recurring_occurrence.cancel", occurrence, previous)
        else:
            if before["status"] == "paused":
                for occurrence in obj.occurrences.filter(
                    status="cancelled", due_date__gte=timezone.localdate()
                ):
                    previous = snapshot(occurrence)
                    occurrence.status = "pending"
                    occurrence.save(update_fields=["status"])
                    audit(membership, "recurring_occurrence.resume", occurrence, previous)
            generate(membership, obj)
        return RecurringOutput(
            rules(membership.household_id).get(pk=obj.pk), context={"membership": membership}
        ).data
    obj = scoped(RecurringOccurrence, membership, pk)
    if obj.status != "pending":
        raise Conflict("Esta ocurrencia ya fue pagada o cancelada.")
    before = snapshot(obj)
    if action == "recurring_occurrence.update":
        if membership.role == "member" and obj.recurring.creator_id != membership.user_id:
            raise PermissionDenied("Sólo podés modificar tus propias recurrencias.")
        obj.amount = data["amount"]
        obj.save(update_fields=["amount"])
    else:
        account = payment_account(membership, data.get("account_id") or obj.recurring.account_id)
        category = obj.recurring.category
        if not category.is_active:
            raise ValidationError({"category_id": "La categoría está archivada."})
        payment = FinancialTransaction.objects.create(
            household_id=membership.household_id,
            creator=membership.user,
            type="expense",
            amount=obj.amount,
            account=account,
            category=category,
            effective_date=data["effective_date"],
            description=f"{obj.recurring.name} · vencimiento {obj.due_date}",
        )
        post_entries(payment)
        audit(membership, "transaction.create", payment)
        obj.payment = payment
        obj.status = "paid"
        obj.save(update_fields=["payment", "status"])
        generate(membership, obj.recurring)
    audit(membership, action, obj, before)
    return OccurrenceOutput(occurrences(membership.household_id).get(pk=obj.pk)).data
