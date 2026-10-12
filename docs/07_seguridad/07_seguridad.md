# 07 · Seguridad, privacidad y aislamiento tenant

## Modelo de amenazas

Principales riesgos: IDOR/BOLA, filtración entre hogares por FK cruzada, escalada de roles, reenvío de invitaciones, duplicación de eventos financieros, XSS/CSRF, exposición de PII en logs/exportaciones, ataques por fuerza bruta y filtración por workers/caché.

## Controles obligatorios MVP

1. Autorización server-side en toda ruta y selector con membresía activa por hogar; denegación por defecto.
2. Pruebas de aislamiento de lectura, escritura, conteos, búsqueda, exportación y filtros. Nunca confiar en el `household_id` del body.
3. Referencias cruzadas con validación de mismo hogar (account/category/card/budget/installment).
4. Sesiones seguras y rotación al autenticar; CSRF adecuado para cookies; protección CORS estricta, TLS/HSTS en producción.
5. Contraseñas con hash robusto por Django; protección de login por tasa de intentos; invitaciones token aleatorio de un solo uso, expirable y hash en BD.
6. Operaciones contables atómicas y claves idempotentes; auditar anulaciones y cambios de permisos.
7. Logs sin credenciales, tokens, notas financieras, valores sensibles ni payload completo. Redacción por defecto.
8. Exportes con autorización y expiración; ficheros temporales privados, borrado tras TTL definido.
9. Validaciones backend independientemente de Angular; sanitizar renderización y establecer política CSP evaluada.
10. Copias cifradas, acceso mínimo, rotación de secretos, recuperación probada, migraciones auditadas.

## Controles operativos

### Controles implementados · Fase 1 financiera

Los endpoints resuelven hogar desde sesión y membresía active; el JSON nunca elige
tenant ni actor. Owner/admin administran; member corrige sólo lo propio; limited_entry
no accede a datos financieros hasta permisos por cuenta. Todas las FKs se consultan
en el hogar y PostgreSQL también rechaza cruces. Escrituras atómicas con bloqueo de
hogar/membresía, idempotencia y revisión esperada. Sesión/CSRF conservados.
[Reglas y evidencia](../10_planificacion/11_nucleo_financiero.md#modelo-y-garantías).

- Admin de Django restringido; sin visibilidad indiscriminada de datos financieros a soporte.
- Usuario administrador de plataforma separado de rol de titular de hogar.
- No volcar datos reales en staging ni tickets; usar datos sintéticos.
- Auditoría de cambios significativos incluyendo actor, tenant, objeto y timestamp.
- Retención y derechos del titular conforme normativa aplicable a mercados de lanzamiento; definición legal pendiente antes de producción pública.
- Borrado de hogar: solicitar confirmación reforzada, revocar accesos, ejecutar política de retención/anominización y backups conforme normativa; no eliminación instantánea ingenua.

## Matriz de amenazas/pruebas

### Revisión ejecutada el 12 de octubre de 2026

El límite de aislamiento es **el hogar**, no el creador de cada registro. Los
miembros autorizados de un mismo hogar comparten su información financiera;
un usuario con varios hogares accede exclusivamente al seleccionado en sesión.
El rol `member` sólo puede corregir/anular sus propios movimientos y modificar
sus propias recurrencias. `limited_entry` sigue sin acceso financiero.

Se revisaron las rutas de cuentas, categorías, movimientos e historial,
transferencias, tarjetas, compras, cuotas/pagos, recurrencias/ocurrencias/pagos,
resumen, identidad, selección y creación de hogares y logout. Las consultas y
referencias de escrituras se restringen al tenant validado en el servidor. El
encabezado `X-Household-ID` comprueba coincidencia con la sesión, nunca concede
acceso. Una membresía revocada se rechaza en la siguiente solicitud.

Refuerzos aplicados:

- El admin global sólo admite usuarios activos con `is_staff` e `is_superuser`.
  Personal con permisos de modelos y titulares/admins de hogares no pueden usarlo
  sin ser superusuarios. Los superusuarios son operadores de confianza con acceso
  global deliberado; las APIs financieras siguen exigiéndoles membresía.
- Respuestas de `/api/`, `/accounts/` y `/admin/`, incluidos errores y redirecciones,
  llevan `Cache-Control: private, no-store, no-cache, max-age=0` y `Vary: Cookie`.
- El resolver de membresía rechaza usuarios desactivados.
- Las rutas hijas privadas vuelven a comprobar autenticación y existencia de
  hogares al navegar dentro de `/app`.

[Pruebas HTTP de seguridad](../../backend/tests/test_route_security.py) cubren
usuarios distintos, sesión apuntando a un tenant sin membresía, membresía
revocada, usuarios con múltiples hogares, detalles/acciones/listados/resúmenes,
CSRF en todas las escrituras implementadas, admin, caché e idempotencia por
usuario/hogar. Se ejecutaron con datos sintéticos en PostgreSQL temporal, separado
de la base de la aplicación. La regresión del backend pasó 84 pruebas, con 12
omisiones explícitas (benchmark opcional y POC de migración); las dos pruebas
posteriores de idempotencia pasaron junto con el conjunto de seguridad (11/11).
El frontend pasó 41 pruebas y las comprobaciones TypeScript; Ruff pasó en los
archivos Python modificados.

Las rutas públicas de landing/login, salud, CSRF, configuración OAuth y esquema
son intencionales y no devuelven registros financieros. Esta revisión corresponde
al código y pruebas locales: no comprueba la configuración de un despliegue,
proxy/CDN, permisos de la cuenta PostgreSQL, backups ni servicios externos. El
aislamiento de consultas está implementado en la aplicación; no hay políticas
PostgreSQL RLS, aunque los triggers existentes validan referencias entre tenants.

| Amenaza | Ejemplo de ataque | Mitigación / test |
|---|---|---|
| IDOR | hogar A consulta transaction UUID de B | queryset tenant scoped; T-01 |
| FK cruzada | gasto A con account B | validar FKs; T-02 |
| Escalada | miembro cambia role a owner | permission class + service; T-03 |
| Doble envío | dos POST simultáneos de gasto | unique idempotency key; T-06 |
| Replay de invitación | aceptar dos veces token | consumed_at + transacción; T-04 |
| Fuga vía búsqueda | texto devuelve transacción B | filtro tenant antes de search; T-01 |
| Resumen duplicado | pago de tarjeta contado como gasto | ledger invariants; T-10 |

## Checklist preproducción

TLS; `DEBUG=False`; `ALLOWED_HOSTS`/CSRF configurados; secretos externos; CORS estricto; backups/restore; dependencia y auditoría de vulnerabilidades; rate limits; logs redactados; pruebas multitenant; revisión de permisos; política de privacidad/Términos; consentimiento y datos personales.
