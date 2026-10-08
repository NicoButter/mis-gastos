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

## Cierre definitivo — 2026-10-08

**Estado de Fase 0: COMPLETADA.** La validación pendiente se ejecutó posteriormente en PostgreSQL `18.6` local, usando la base aislada de proyecto `gastio_db`.

| Verificación | Resultado confirmado |
|---|---|
| Suite backend | `python -m pytest -v`: **9 aprobadas, 0 fallidas, 1.60 s** |
| Django | `python manage.py check`: sin problemas |
| Migraciones | Iniciales aplicadas correctamente |
| Frontend | Lint, build y pruebas aprobadas durante Fase 0 |

La suite backend se ejecuta con **pytest**, desde `backend/` o mediante el archivo de configuración `backend/pyproject.toml`. El comando reproducible desde la raíz es:

```bash
set -a; source .env; set +a
.venv/bin/python -m pytest -v -c backend/pyproject.toml backend
```

`manage.py test` no es actualmente un punto de entrada equivalente ni soportado para esta suite. `manage.py` selecciona `config.settings.development` por defecto y Django usa `DiscoverRunner` basado en `unittest`; las pruebas existentes son funciones pytest y dependen de marcadores `pytest.mark.django_db` y de la configuración `DJANGO_SETTINGS_MODULE=config.settings.test` declarada en `pyproject.toml`. No se modificó el runner, porque no hay una necesidad demostrada de duplicar o migrar la suite.

No queda un riesgo técnico bloqueante para iniciar Fase 1. Como decisión de diseño ya identificada, ADR-003 (política final de autenticación SPA/cookies/CSRF) debe ratificarse antes de implementar los flujos de registro, inicio de sesión e invitaciones de esa fase.

## Auditoría de cierre previa — contexto del sandbox

La siguiente evidencia se conserva como registro de la auditoría realizada en un sandbox que impedía conexiones PostgreSQL. Esa limitación quedó resuelta por la ejecución posterior confirmada anteriormente; no describe el estado final de Fase 0.

### Diagnóstico del entorno

| Componente | Resultado |
|---|---|
| Python / Django | Python `3.14.8`, Django `5.2.18` |
| Node / Angular | Node `22.23.0`; Angular `21.2.x` declarado y build verificado previamente |
| PostgreSQL cliente / servidor instalado | `psql`, `pg_isready`, `postgres` e `initdb` `18.6` disponibles |
| Instancia local | No utilizable: no hay proceso ni listener TCP en `127.0.0.1:5432`; el socket visible en `/run/postgresql/.s.PGSQL.5432` no responde |
| Servicios del sistema | La consulta a systemd fue denegada por el sandbox; no se modificó ningún servicio |
| Credenciales de proyecto | No existe `.env` local; solo `.env.example`, sin secretos reales |

Se intentó iniciar un clúster exclusivo en un directorio temporal bajo `/tmp`, sin afectar servicios ni datos existentes. El sandbox denegó la creación tanto de sockets TCP como Unix (`Operation not permitted`). El directorio temporal se eliminó tras el intento; no quedó instancia ni base creada.

### Configuración y migraciones

- Django usa `config.settings.development` por defecto; `DATABASE_URL` es obligatorio y solo acepta `postgres`/`postgresql`.
- En tests, `config.settings.test` mantiene PostgreSQL y `DATABASE_TEST_NAME`; no existe fallback a SQLite.
- `makemigrations --check --dry-run` informa **sin cambios pendientes**. La comprobación de historial no pudo conectarse al servidor, por la limitación indicada.
- Las únicas migraciones de dominio son `accounts.0001_initial` y `households.0001_initial`; no se añadieron módulos financieros.
- Se corrigió el parser de `DATABASE_URL` para admitir el parámetro estándar `?host=/ruta/del/socket&port=...`, útil para ejecución aislada local/CI.

### Resultado de pruebas real

| Grupo | Resultado | Evidencia |
|---|---|---|
| Configuración sin DB | 3 aprobadas | PostgreSQL obligatorio, rechazo de SQLite y socket Unix |
| OpenAPI | 1 aprobada | `/api/v1/schema/` responde y declara `Gastio API` |
| Usuario, salud, hogares, membresías y roles | 5 con error de infraestructura | El runner no puede crear la DB de tests porque PostgreSQL no acepta conexiones |
| Suite Django total | **4 aprobadas, 5 errores, 0 fallos de aserción** | `OperationalError: connection ... Operation not permitted` |
| Ruff / Black | Correctos | Revisión de todo `backend/` |
| Producción | Correcto en revisión de configuración | `DEBUG=False`, cookies de sesión/CSRF seguras y HTTPS activo |

Los cinco casos pendientes cubren usuario personalizado, health con consulta real, usuario sin membresía, aislamiento de consulta de un usuario multi-hogar y denegación de administración a rol limitado. No se obtuvo un resultado funcional de esos casos todavía: todos se detienen antes de ejecutar por la conexión PostgreSQL.

### Seguridad y aislamiento revisados

- El tenant se resuelve en `resolve_active_membership()` con usuario autenticado, UUID válido y membresía `active` antes de consultar datos del hogar.
- Un no miembro recibe `404` para reducir enumeración; la falta de permiso de operación produce `403`; las respuestas de error son envoltorios genéricos sin payload tenant.
- `tenant_queryset()` impone `household_id` sobre la consulta, y `HasHouseholdPermission` guarda solamente la membresía validada en el request. Angular no participa en esa decisión.
- Las pruebas implementadas incluyen no miembro, membresía multi-hogar y rol de carga limitada; su ejecución contra PostgreSQL sigue pendiente por el bloqueo de infraestructura.
- Autenticación de sesión con cookies `HttpOnly` y `SameSite=Lax`; el interceptor frontend envía CSRF solo en mutaciones. No hay endpoint de login en Fase 0.
- Producción fuerza `DEBUG=False`, HTTPS, HSTS y cookies seguras. Como corrección de auditoría, ahora rechaza `*` en `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS`.

### Entorno aislado reproducible

En una máquina Fedora con PostgreSQL en ejecución, crear exclusivamente el rol temporal de test. La contraseña se toma de una variable de entorno, nunca se guarda en el repositorio:

```bash
export GASTIO_TEST_DB_PASSWORD='generar-una-clave-larga-y-unica'
sudo -u postgres psql -v ON_ERROR_STOP=1 -v db_password="$GASTIO_TEST_DB_PASSWORD" <<'SQL'
CREATE ROLE gastio_phase0_test LOGIN PASSWORD :'db_password' NOSUPERUSER NOCREATEROLE NOBYPASSRLS NOINHERIT CREATEDB;
SQL
```

`CREATEDB` es el único privilegio adicional requerido para que Django cree y elimine su base efímera `gastio_phase0_test`. El rol no tiene superusuario, administración de roles ni acceso concedido a otras bases. Luego:

```bash
export DATABASE_URL="postgresql://gastio_phase0_test:${GASTIO_TEST_DB_PASSWORD}@127.0.0.1:5432/postgres"
export DATABASE_TEST_NAME=gastio_phase0_test
export DJANGO_SECRET_KEY='solo-para-tests-locales'
.venv/bin/python -m pytest -c backend/pyproject.toml backend
.venv/bin/python backend/manage.py showmigrations accounts households
```

Al finalizar, Django elimina la base de tests. Para retirar el rol temporal:

```bash
sudo -u postgres psql -c 'DROP ROLE gastio_phase0_test;'
```

### Limitación histórica y condición de cierre original

El único bloqueo registrado era disponer de PostgreSQL accesible para el usuario ejecutor o de Docker/CI con sockets permitidos. Se resolvió mediante la ejecución posterior de **9/9 pruebas aprobadas**, migraciones aplicadas y health verificado con PostgreSQL real.

## Evidencia de verificación previa

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
