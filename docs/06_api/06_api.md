# 06 · Contrato REST API v1 (propuesta)

Las rutas de tarjetas, cuotas, pagos y presupuestos de esta tabla son un boceto
histórico y no están implementadas. La propuesta vigente para tarjetas está en
[Diseño Fase 2.0](../10_planificacion/13_diseno_fase_2_tarjetas_cuotas.md), aún
sujeta a ratificación; no constituye contrato operativo ni esquema OpenAPI.

Base `/api/v1/`; JSON; autenticación obligatoria salvo endpoints públicos; OpenAPI generado desde backend como fuente definitiva. IDs UUID; paginación; respuestas con códigos y errores consistentes.

## Rutas

| Método | Ruta | Propósito |
|---|---|---|
| GET | `/auth/me/` | Usuario y membresías |
| POST | `/auth/logout/` | Cerrar sesión |
| POST | `/households/` | Crear explícitamente el primer hogar y su membresía owner durante onboarding |
| GET/PATCH | `/households/{hid}/` | Consultar/editar hogar |
| GET/POST | `/households/{hid}/invitations/` | Invitaciones |
| POST | `/invitations/{token}/accept/` | Aceptar invitación (token tratado como secreto) |
| GET/PATCH | `/households/{hid}/members/{id}/` | Membresías y permisos |
| GET/POST | `/households/{hid}/accounts/` | Cuentas |
| GET/POST | `/households/{hid}/categories/` | Categorías |
| GET/POST | `/households/{hid}/transactions/` | Listar/crear movimientos |
| GET/PATCH | `/households/{hid}/transactions/{id}/` | Detalle/corrección |
| POST | `/households/{hid}/transactions/{id}/void/` | Anular |
| POST | `/households/{hid}/transfers/` | Transferir |
| GET/POST | `/households/{hid}/cards/` | Tarjetas |
| GET/POST | `/households/{hid}/card-purchases/` | Compras y cuotas |
| GET | `/households/{hid}/installments/?year=&month=` | Obligaciones futuras |
| POST | `/households/{hid}/card-payments/` | Pagar tarjeta |
| GET/POST | `/households/{hid}/budgets/` | Presupuestos |
| GET | `/households/{hid}/dashboard/?from=&to=` | Resumen del hogar |
| GET | `/health/` | Salud básica sin datos privados |
| GET | `/auth/config/` | Disponibilidad no sensible de Google OAuth |
| GET | `/auth/csrf/` | Entrega/fija token CSRF |
| POST | `/auth/active-household/` | Selecciona hogar activo validado por servidor |

## Ejemplo de gasto

### Contrato implementado · Fase 1 financiera

Las rutas financieras propuestas arriba eran conceptuales. El contrato vigente usa
`/api/v1/accounts/`, `/categories/`, `/transactions/`, `/transfers/` y
`/dashboard/summary/`, con hogar autorizado desde la sesión y campos snake_case.
En el body se usa `description` (no `note`), la moneda se deriva de la cuenta;
`Idempotency-Key` UUID es obligatorio para todas las escrituras financieras.
PATCH/void usa `expected_revision`; auditoría en `transactions/{id}/history/`.
Listas paginadas 25, máximo 100; detalles/filtros/códigos en
[contrato operativo](../10_planificacion/11_nucleo_financiero.md#api-implementada).

```json
POST /api/v1/households/{hid}/transactions/
Idempotency-Key: 8c04...UUID
{
  "type": "expense",
  "amount": "18500.00",
  "currency": "ARS",
  "effective_date": "2026-10-08",
  "account_id": "uuid",
  "category_id": "uuid",
  "note": "Compra supermercado"
}
```

**201** devuelve recurso con ID; **200** al replay idempotente documentado; **400** formato/reglas inválidas; **401** anónimo; **403/404** sin permiso o recurso invisible; **409** conflicto (idempotency key reutilizada con payload diferente).

## Esquema de error recomendado

```json
{"error":{"code":"VALIDATION_ERROR","message":"Datos inválidos","fields":{"amount":["Debe ser positivo"]},"request_id":"uuid"}}
```

## Reglas transversales

- Nada de `household_id` arbitrario en payload que pueda sustituir al tenant de ruta.
- La API no confía en `role`, `user_id` o `balance` enviados por cliente.
- Cursor/paginación y filtros acotados con límites y orden estable por fecha+ID.
- Dates `YYYY-MM-DD`; instantes `ISO 8601` con zona; importes como cadena decimal.
- Escritura con idempotencia para mobile; mutations transaccionales.
- OpenAPI + pruebas de contrato; esta tabla sirve como diseño inicial, no código ejecutable.

## Tarjetas simples

Endpoints bajo `/api/v1/`, con sesión y hogar activo:

- `credit-cards/`: GET/POST; `credit-cards/{id}/`: GET/PATCH. Campos:
  `bank`, `name`, `closing_day`, `due_day`, `is_active`.
- `card-purchases/`: GET/POST; detalle GET. Alta: `card_id`, `category_id`
  (gasto activa), `description`, `amount`, `purchase_date`, `installments_count`
  (1–120). Devuelve cuotas con importes, cierres, vencimientos y pendiente.
- `card-installments/`: GET y detalle GET;
  `card-installments/{id}/pay/`: POST con `account_id` y `effective_date`.
  Paga la cuota completa, retorna el pago y la cuenta. Segundo pago con otra clave:
  409. Reintento idéntico con la misma clave: 200, sin descontar nuevamente.

Listados paginados. Todas las escrituras requieren `Idempotency-Key` UUID y admiten
`X-Household-ID` para detectar cambios de hogar. El resumen agrega `card_pending`
y `upcoming_installments` (hasta ocho pendientes, vencidas primero). Sus gastos y
categorías incluyen cuotas del mes por vencimiento, independientemente del pago.
Pagos visibles como `card_payment` en movimientos, sin edición ni anulación genérica.

## Resumen financiero y cuentas

`GET dashboard/summary/?month=YYYY-MM` conserva los totales mensuales de operaciones
vigentes y cuotas por vencimiento; aperturas, transferencias y pagos de tarjetas no
suman ingresos ni gastos. `available_balances` agrega importes por moneda de cuentas
activas de efectivo, banco y billetera. El núcleo admite actualmente sólo ARS.
`balance` conserva su significado anterior (saldo consolidado de todas las cuentas).
Ambos son saldos actuales del núcleo, independientes del período seleccionado.

`GET accounts/?month=YYYY-MM` y `GET accounts/{id}/?month=YYYY-MM` agregan `month`,
`monthly_inflow`, `monthly_outflow`, `monthly_income`, `monthly_expense`,
`monthly_opening`, `monthly_transfer_in`, `monthly_transfer_out` y
`monthly_card_payments`, usando sólo entradas de la revisión vigente no anulada.
Entradas/salidas incluyen aperturas y transferencias; ingresos/gastos las excluyen.
Los pagos de tarjeta son salidas y se detallan separadamente, pues las cuotas ya
integran los gastos del hogar. Sin período se usa el mes local actual; un período
inválido devuelve 400. No se incorporan modelos ni migraciones.
