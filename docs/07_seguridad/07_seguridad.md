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

- Admin de Django restringido; sin visibilidad indiscriminada de datos financieros a soporte.
- Usuario administrador de plataforma separado de rol de titular de hogar.
- No volcar datos reales en staging ni tickets; usar datos sintéticos.
- Auditoría de cambios significativos incluyendo actor, tenant, objeto y timestamp.
- Retención y derechos del titular conforme normativa aplicable a mercados de lanzamiento; definición legal pendiente antes de producción pública.
- Borrado de hogar: solicitar confirmación reforzada, revocar accesos, ejecutar política de retención/anominización y backups conforme normativa; no eliminación instantánea ingenua.

## Matriz de amenazas/pruebas

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
