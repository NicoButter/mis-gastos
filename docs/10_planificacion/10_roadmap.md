# 10 · Roadmap, backlog y decisiones

## Secuencia de entregas para Codex

| Fase | Entregable | Criterios de salida |
|---|---|---|
| 0 ✓ Completada | Scaffolding monorepo, configs, env, CI, salud y README | Backend/frontend arrancan, PostgreSQL conecta, tests base verdes (9/9 backend con PostgreSQL 18.6) |
| 0.5 ✓ Completada | Landing pública, rutas SaaS y preparación OAuth | Navegación pública, 404, rutas privadas protegidas y frontend verificado |
| 0.6 En validación externa | Google OAuth/OIDC con Allauth y sesión Django | Credenciales reales, callback Google y suite PostgreSQL pendientes de ejecutar fuera del sandbox |
| 1 | Usuarios, hogares, memberships y permisos | Dos hogares aislados; invitaciones y roles probados |
| 2 | Cuentas, categorías, transacciones/ledger, listado | Importes consistentes, idempotencia y pruebas cruzadas |
| 3 | Carga rápida móvil y dashboard básico | Flujo responsive real, estados de error, balance confiable |
| 4 | Tarjetas, cuotas, pagos y proyección | No doble contabilización, reglas temporales y redondeo probados |
| 5 | Presupuestos, filtros/reportes y auditoría | Todas las funcionalidades Must trazadas y pruebas E2E |
| 6 | Staging, performance, seguridad y revisión integral | Checklist preproducción, backup/restore, datos sintéticos |
| V1 | Recurrentes, cierre diario, objetivos y exportaciones | Especificar nuevos RF antes de construir |
| Futuro | IA, OCR, offline, pagos SaaS, bancos | ADR, análisis legal/seguridad y priorización comercial |

## Cierre de Fase 0

- Cerrada el 2026-10-08 tras validar `python -m pytest -v`: 9 aprobadas, 0 fallidas en 1.60 s, sobre PostgreSQL 18.6 y `gastio_db`.
- `python manage.py check` no reportó problemas y las migraciones iniciales quedaron aplicadas.
- El runner oficial permanece en pytest; `manage.py test` no interpreta los marcadores ni la configuración de `pytest-django` de la suite actual.
- Sin bloqueos técnicos para iniciar Fase 1. ADR-003 se debe ratificar antes de construir los flujos de autenticación e invitaciones.

## Iteración 0.5 · Landing y rutas

- Cerrada el 2026-10-08: landing en `/`, login en `/login`, 404 explícito y shell privado bajo `/app`.
- La integración Google OAuth/OIDC no se implementó: `AuthService` deja el estado anónimo y reserva el contrato de sesión para Django/Allauth.
- Verificado con `npm --prefix frontend run lint`, `npm --prefix frontend test -- --reporters=verbose` (6 pruebas) y `npm --prefix frontend run build`.

## Iteración 0.6 · Autenticación Google

- Implementada sobre `django-allauth` 65.x: sesión Django/CSRF, PKCE, `state`, scopes mínimos `openid email profile` y sin JWT ni almacenamiento web de tokens.
- Se añadieron los endpoints de sesión, cierre, CSRF, capacidad de configuración y selección de hogar validada; el adaptador impide unir identidades por coincidencia de email.
- La verificación OAuth real requiere cargar las dos credenciales de Google Cloud y registrar exactamente `http://localhost:8000/accounts/google/login/callback/`.
- No se marca como cerrada hasta ejecutar migraciones Allauth y pytest completo contra PostgreSQL accesible, además de la prueba manual real. Véase `docs/07_seguridad/08_google_oauth.md`.

## Backlog inicial

**Épica E-01 Plataforma**: scripts start/test/lint, settings dev/prod, OpenAPI, logging, health, CI.

**E-02 Tenant**: Household + Membership; backend permission service; invitación; selección hogar; pruebas contra IDOR.

**E-03 Contabilidad**: Account/Category, Transaction/LedgerEntry, transferencia, reversión, saldos derivados, idempotencia.

**E-04 Experiencia**: layouts responsive, dashboard, movimientos y quick expense.

**E-05 Tarjetas**: política de ciclos, compras/cuotas, pagos y obligaciones futuras.

**E-06 Gestión**: presupuestos, reportes y auditoría de cambios.

## ADR a resolver antes de su fase

| ADR | Momento límite | Default temporal |
|---|---|---|
| 001 Privacidad por cuenta | Antes de fase 1 | Roles por hogar; cargador ve solo cuentas asignadas |
| 002 Ledger y tarjeta | Antes de fase 2/4 | Libro por entradas, deuda diferenciada; pagos no son gastos |
| 003 Auth SPA | Antes de fase 1 | Preferir cookie segura y CSRF; documentar alternativa |
| 004 Política de saldo negativo | Antes de fase 2 | Permitir saldo negativo con advertencia, no como crédito real |
| 005 Deuda y pagos parciales | Antes de fase 4 | Admitir pago parcial, validar sobrepago |
| 006 Multidivisa | Antes de activar otras monedas | ARS única operativa en MVP |
| 007 Licenciamiento SaaS | Antes de comercializar | Plan interno sin cobro ni cuotas en MVP |

## Prompt de arranque para Codex

> Lee íntegramente `README.md` y `docs/` de Gastio. Implementá **solo fase 0**: un monorepo funcional con backend Django/DRF, PostgreSQL, frontend Angular/Tailwind, configuración por entorno, salud, CORS/CSRF acorde a auth futura, base para test/lint/CI y estructura modular indicada. No crees entidades financieras, migraciones de negocio, pantallas completas, OAuth ni features V1/futuro. No instales servicios innecesarios en el VPS. Conservá este paquete documental, redactá `docs/10_planificacion/estado_implementacion.md` con evidencia de comandos ejecutados y decisiones técnicas, e informá cómo reproducir la instalación local. Antes de codificar, señalá incompatibilidades de versiones y resolvélas eligiendo versiones estables soportadas.

## Gestión de cambios

Cada cambio de alcance debe actualizar ERS, caso de uso, modelo de datos/API y prueba relacionada en el mismo PR. No mezclar documentación deseada con funcionalidad existente.
