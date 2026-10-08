# Gastio — Documentación base del producto

**Estado:** propuesta técnica v0.1 · **Fecha:** 2026-10-08 · **Responsable:** Vetrabyte

Gastio es un SaaS multitenant de finanzas personales y familiares, con una experiencia completa de administración y una interfaz móvil de carga rápida. Se implementará como monolito modular en un único repositorio (backend Django/DRF, frontend Angular/Tailwind, PostgreSQL).

## Índice de lectura recomendado

1. [Visión y alcance](docs/01_producto/01_vision_alcance.md)
2. [Especificación de requisitos](docs/02_requisitos/02_ers.md)
3. [Casos de uso](docs/03_casos_uso/03_casos_uso.md)
4. [Arquitectura](docs/04_arquitectura/04_arquitectura.md)
5. [Modelo de datos](docs/05_datos/05_modelo_datos.md)
6. [Contrato API](docs/06_api/06_api.md)
7. [Seguridad y multitenancy](docs/07_seguridad/07_seguridad.md)
8. [UX y pantallas](docs/08_ux/08_ux.md)
9. [Plan de pruebas](docs/09_calidad/09_pruebas.md)
10. [Roadmap, backlog y decisiones](docs/10_planificacion/10_roadmap.md)

## Convenciones

- **MVP**: entrega inicial; **V1**: incremento posterior; **Futuro**: no autorizado para primera entrega.
- Requisitos: `RU` usuario, `RF` funcional, `RNF` no funcional, `RS` sistema, `RN` regla de negocio.
- Prioridad **Must/Should/Could**; cada requisito tiene criterios verificables.
- Todas las decisiones abiertas están señaladas con `ADR pendiente` y se pueden implementar con defaults explícitos sin bloquear el scaffolding.
- Datos de ejemplo y montos son ilustrativos, no operativos.

## Condición de inicio de implementación

Codex debe leer **todos** estos archivos y construir primero un esqueleto ejecutable. No desarrollar pagos, IA, OCR, conexiones bancarias o sincronización offline sin aceptación de una fase posterior.

## Desarrollo local — Fase 0

Requisitos en Fedora: Python 3.14, Node 22.23+, PostgreSQL 17 y opcionalmente Redis 7. Docker Compose solo facilita levantar PostgreSQL/Redis; no es requisito para ejecutar la aplicación.

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up -d  # alternativa: servicios locales
./scripts/setup.sh
set -a; source .env; set +a
.venv/bin/python backend/manage.py migrate
./scripts/run-backend.sh
```

En otra terminal:

```bash
npm --prefix frontend start
```

La API de salud queda en `http://127.0.0.1:8000/api/v1/health/` y la interfaz en `http://localhost:4200/`.

Para verificaciones reproducibles:

```bash
set -a; source .env; set +a
.venv/bin/python -m pytest -c backend/pyproject.toml backend
.venv/bin/python -m ruff check backend
.venv/bin/python -m black --check backend
npm --prefix frontend run build
```

La configuración requiere `DATABASE_URL` PostgreSQL de forma explícita y no usa SQLite como alternativa. Consultá el [estado de implementación](docs/10_planificacion/estado_implementacion.md) para decisiones, supuestos y evidencia.
