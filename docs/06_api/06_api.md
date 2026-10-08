# 06 · Contrato REST API v1 (propuesta)

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
