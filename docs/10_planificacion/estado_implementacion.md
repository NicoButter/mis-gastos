# Estado de implementación — Fase 0

**Fecha:** 2026-10-08  
**Alcance ejecutado:** fundación técnica; no se implementaron entidades ni operaciones financieras.

## Decisiones y compatibilidad

- Django `5.2.x` LTS, DRF `3.16.x` y Python `3.14`: Django 5.2 soporta Python 3.14 desde 5.2.8 ([notas oficiales](https://docs.djangoproject.com/en/5.2/releases/5.2/)).
- Angular `21.2.x`, TypeScript `5.9.x` y Node `22.23.0`: Node 22.23 cumple el mínimo `^22.12` publicado para Angular 21 ([matriz oficial](https://angular.dev/reference/versions)).
- PostgreSQL es obligatorio tanto en desarrollo como tests. No hay fallback a SQLite: la configuración falla si `DATABASE_URL` no es PostgreSQL.
- ADR-003 se resuelve temporalmente con autenticación de sesión/cookie y CSRF. El usuario personalizado por email ya evita una migración incompatible al incorporar Django Allauth/OAuth Google; esas integraciones no se activaron.
- Los roles se guardan en `HouseholdMembership`. La resolución de tenant se centraliza en `resolve_active_membership()` antes de hacer queries; los futuros modelos deben usar `tenant_queryset()` y `HasHouseholdPermission`.

## Implementado

- Monorepo con `backend/`, `frontend/`, `infra/`, `scripts/` y CI.
- Settings Django separados para desarrollo, tests y producción; CORS/CSRF de allowlist explícita, logging correlacionable sin payloads y envoltorio de errores.
- Usuario UUID/email y los únicos modelos fundacionales: `Household` y `HouseholdMembership`; no existe creación automática de hogares.
- Endpoint público de readiness `GET /api/v1/health/`; esquema OpenAPI disponible en `/api/v1/schema/`.
- Celery/Redis preparado, sin tareas funcionales.
- Angular standalone con rutas, guard, interceptores de cookie/CSRF, layout público, login placeholder, shell privado responsive, selector de hogar controlado, modo completo y modo rápido sin persistencia financiera.
- Manifest PWA mínimo sin cachear API ni inventar iconos finales.

## Supuestos conservadores

- La creación de hogares, invitaciones, login y la selección persistida del hogar pertenecen a Fase 1. Se dejó la infraestructura para implementarlas transaccionalmente sin crear hogares implícitos.
- Los módulos de finanzas posteriores están presentes como límites de dominio, pero no se añaden a `INSTALLED_APPS`, no tienen modelos ni migraciones.
- Un tenant no miembro devuelve 404 al resolver contexto para reducir enumeración; los permisos de operación devuelven 403.

## Evidencia de verificación

Ejecutado el 2026-10-08:

- `npm --prefix frontend ci`: instalación limpia y lockfile reproducible.
- `npm --prefix frontend run lint`: correcto.
- `npm --prefix frontend run build`: correcto.
- `npm --prefix frontend test -- --reporters=verbose`: **1 archivo / 1 prueba correcta**.
- `npm --prefix frontend audit --json`: **0 vulnerabilidades**.
- `python backend/manage.py check`: correcto con configuración PostgreSQL explícita.
- `python backend/manage.py makemigrations --check --dry-run`: sin cambios pendientes. Django emitió solamente un warning al no poder comprobar el historial contra un servidor PostgreSQL inexistente en este entorno.
- `ruff check backend` y `black --check` por archivo: correctos.

La suite `pytest` de backend fue iniciada y validó el test de configuración, pero no pudo crear la base de tests para los cinco tests que requieren datos: `127.0.0.1:5432` no responde y este entorno no dispone de Docker. Es intencional que no exista un fallback SQLite. Para ejecutar la suite completa, iniciar PostgreSQL local o `docker compose -f infra/docker-compose.yml up -d`, cargar `.env` y correr `python -m pytest -c backend/pyproject.toml backend`.
