import hashlib
import json
from decimal import Decimal
from uuid import UUID

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.text import slugify
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError

from apps.audit.models import AuditEvent
from apps.categories.models import Category
from apps.households.models import Household, HouseholdMembership
from apps.households.services import resolve_active_membership
from apps.wallets.models import FinancialAccount

from .models import FinancialTransaction, LedgerEntry, WriteReceipt
from .serializers import AccountOutput, CategoryOutput, OperationOutput


class Conflict(APIException):
    status_code = 409
    default_detail = "La operación cambió o la clave de idempotencia ya fue utilizada."
    default_code = "CONFLICT"


def authorize(membership, manage=False):
    if membership.role not in ({"owner", "admin"} if manage else {"owner", "admin", "member"}):
        raise PermissionDenied("Permiso financiero insuficiente.")


def accounts(household_id):
    return FinancialAccount.objects.filter(household_id=household_id).annotate(
        balance=Coalesce(
            Sum(
                "entries__amount",
                filter=Q(
                    entries__transaction__status="posted",
                    entries__revision=F("entries__transaction__revision"),
                ),
            ),
            Value(Decimal("0")),
            output_field=DecimalField(max_digits=24, decimal_places=2),
        )
    )


def operations(household_id):
    return FinancialTransaction.objects.filter(household_id=household_id).select_related(
        "account", "destination", "category", "creator"
    )


def snapshot(obj):
    from django.forms.models import model_to_dict

    return json.loads(json.dumps(model_to_dict(obj), cls=DjangoJSONEncoder))


def audit(membership, action, obj, before=None):
    AuditEvent.objects.create(
        household_id=membership.household_id,
        actor=membership.user,
        action=action,
        object_type=obj._meta.model_name,
        object_id=obj.pk,
        before=before or {},
        after=snapshot(obj),
    )


def scoped(model, membership, pk):
    try:
        return model.objects.get(household_id=membership.household_id, pk=pk)
    except model.DoesNotExist as exc:
        raise NotFound("Recurso no encontrado.") from exc


def validate_operation(membership, data):
    account = scoped(FinancialAccount, membership, data["account_id"])
    if not account.is_active:
        raise ValidationError({"account_id": "La cuenta está archivada."})
    destination = category = None
    if data["type"] == "transfer":
        if data.get("category_id") or not data.get("destination_id"):
            raise ValidationError(
                {"destination_id": "Elegí destino; la transferencia no tiene categoría."}
            )
        destination = scoped(FinancialAccount, membership, data["destination_id"])
        if (
            destination == account
            or not destination.is_active
            or destination.currency != account.currency
        ):
            raise ValidationError(
                {"destination_id": "Debe ser otra cuenta activa de la misma moneda."}
            )
    else:
        if data.get("destination_id") or not data.get("category_id"):
            raise ValidationError(
                {"category_id": "Elegí una categoría; no corresponde cuenta destino."}
            )
        category = scoped(Category, membership, data["category_id"])
        if not category.is_active or category.type != data["type"]:
            raise ValidationError({"category_id": "Categoría inactiva o de otro tipo."})
    return {
        "account": account,
        "destination": destination,
        "category": category,
        "currency": account.currency,
    }


def post_entries(obj):
    sign = -1 if obj.type in {"expense", "transfer"} else 1
    entries = [
        LedgerEntry(
            household_id=obj.household_id,
            transaction=obj,
            revision=obj.revision,
            account=obj.account,
            amount=obj.amount * sign,
        )
    ]
    if obj.destination_id:
        entries.append(
            LedgerEntry(
                household_id=obj.household_id,
                transaction=obj,
                revision=obj.revision,
                account=obj.destination,
                amount=obj.amount,
            )
        )
    LedgerEntry.objects.bulk_create(entries)


@transaction.atomic
def write(user, household_id, key, action, data, pk=None):
    """Lock one household for deterministic concurrent writes and retry receipts."""
    try:
        key = UUID(str(key))
    except (ValueError, TypeError) as exc:
        raise ValidationError({"Idempotency-Key": "Se requiere una clave UUID."}) from exc
    Household.objects.select_for_update().get(pk=household_id)
    membership = resolve_active_membership(user, household_id)
    membership = HouseholdMembership.objects.select_for_update().get(pk=membership.pk)
    if membership.status != "active":
        raise PermissionDenied("La membresía ya no está activa.")
    authorize(membership, manage=action.startswith(("account", "category")))
    fingerprint = hashlib.sha256(
        json.dumps(
            {"action": action, "pk": str(pk), "data": data}, cls=DjangoJSONEncoder, sort_keys=True
        ).encode()
    ).hexdigest()
    receipt = WriteReceipt.objects.filter(household_id=household_id, actor=user, key=key).first()
    if receipt:
        if receipt.fingerprint != fingerprint:
            raise Conflict()
        return receipt.response, True
    if action == "account.create":
        fields = dict(data)
        opening = fields.pop("opening_balance")
        date = fields.pop("opening_date")
        if not fields.get("is_active", True):
            raise ValidationError({"is_active": "Creá la cuenta activa antes de archivarla."})
        obj = FinancialAccount.objects.create(household_id=household_id, **fields)
        audit(membership, action, obj)
        if opening:
            operation = FinancialTransaction.objects.create(
                household_id=household_id,
                creator=user,
                type="opening",
                amount=opening,
                account=obj,
                effective_date=date,
                description="Saldo inicial",
            )
            post_entries(operation)
            audit(membership, "opening.create", operation)
        result = AccountOutput(accounts(household_id).get(pk=obj.pk)).data
    elif action == "account.update":
        obj = scoped(FinancialAccount, membership, pk)
        if set(data) - {"name", "kind", "description", "is_active"}:
            raise ValidationError("La moneda y apertura no se pueden modificar.")
        before = snapshot(obj)
        for field, value in data.items():
            setattr(obj, field, value)
        obj.save()
        audit(membership, action, obj, before)
        result = AccountOutput(accounts(household_id).get(pk=obj.pk)).data
    elif action.startswith("category"):
        if action == "category.create":
            fields = dict(data)
            fields.setdefault("slug", f'{data["type"]}-{slugify(data["name"])}')
            if Category.objects.filter(household_id=household_id, slug=fields["slug"]).exists():
                raise ValidationError({"slug": "Este identificador ya existe."})
            obj = Category.objects.create(household_id=household_id, **fields)
            before = {}
        else:
            obj = scoped(Category, membership, pk)
            if "slug" in data or ("type" in data and data["type"] != obj.type):
                raise ValidationError("El identificador y tipo de categoría son estables.")
            before = snapshot(obj)
            for field, value in data.items():
                setattr(obj, field, value)
            obj.save()
        audit(membership, action, obj, before)
        result = CategoryOutput(obj).data
    else:
        if action == "transaction.create":
            if "expected_revision" in data:
                raise ValidationError("La revisión sólo corresponde a correcciones.")
            fields = validate_operation(membership, data)
            obj = FinancialTransaction.objects.create(
                household_id=household_id,
                creator=user,
                **fields,
                **{k: data[k] for k in ["type", "amount", "effective_date", "description"]},
            )
            post_entries(obj)
            before = {}
        else:
            obj = scoped(FinancialTransaction, membership, pk)
            if membership.role == "member" and obj.creator_id != user.pk:
                raise PermissionDenied("Sólo podés corregir tus propios movimientos.")
            if obj.type == "opening":
                raise ValidationError(
                    "La apertura es inmutable; registrá una operación de ajuste explícita."
                )
            if obj.revision != data.get("expected_revision"):
                raise Conflict()
            if obj.status == "voided":
                raise Conflict("El movimiento ya está anulado.")
            before = snapshot(obj)
            if action == "transaction.void":
                obj.status = "voided"
            else:
                merged = {
                    "type": obj.type,
                    "amount": obj.amount,
                    "account_id": obj.account_id,
                    "destination_id": obj.destination_id,
                    "category_id": obj.category_id,
                    "effective_date": obj.effective_date,
                    "description": obj.description,
                    **data,
                }
                if merged["type"] != obj.type:
                    raise ValidationError("El tipo de operación es inmutable.")
                for field, value in validate_operation(membership, merged).items():
                    setattr(obj, field, value)
                for field in ["amount", "effective_date", "description"]:
                    setattr(obj, field, merged[field])
                obj.revision += 1
            obj.save()
            if obj.status == "posted":
                post_entries(obj)
        audit(membership, action, obj, before)
        result = OperationOutput(
            operations(household_id).get(pk=obj.pk), context={"membership": membership}
        ).data
    result = json.loads(json.dumps(result, cls=DjangoJSONEncoder))
    WriteReceipt.objects.create(
        household_id=household_id, actor=user, key=key, fingerprint=fingerprint, response=result
    )
    return result, False
