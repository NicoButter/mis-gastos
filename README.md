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

El núcleo financiero de Fase 1 ya conecta cuentas, categorías, movimientos,
transferencias, carga rápida y dashboard a PostgreSQL. Ver
[arquitectura, API y recorrido manual](docs/10_planificacion/11_nucleo_financiero.md).
La [auditoría Fase 1.1](docs/10_planificacion/12_estabilizacion_fase_1_1.md)
registra las correcciones, E2E real, mediciones y riesgos pendientes.

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
./scripts/dev-start.sh
```

`dev-start.sh` carga `.env`, comprueba Django y la conexión a PostgreSQL, aplica las migraciones pendientes y levanta el backend y el frontend con logs identificados. Con `Ctrl+C` detiene ambos procesos. No instala ni inicia servicios del sistema; PostgreSQL debe estar disponible antes de ejecutarlo. La API de salud queda en `http://127.0.0.1:8000/api/v1/health/` y la interfaz en `http://localhost:4200/`.

Redis y Celery son opcionales en la Fase 0 y no se inician mediante ese script. Para levantar los servicios manualmente y conservar los logs separados, se puede seguir usando `./scripts/run-backend.sh` y `npm --prefix frontend start` en terminales distintas.

Para verificaciones reproducibles:

```bash
set -a; source .env; set +a
.venv/bin/python -m pytest -c backend/pyproject.toml backend
.venv/bin/python -m ruff check backend
.venv/bin/python -m black --check backend
npm --prefix frontend run build
```

La configuración requiere `DATABASE_URL` PostgreSQL de forma explícita y no usa SQLite como alternativa. Consultá el [estado de implementación](docs/10_planificacion/estado_implementacion.md) para decisiones, supuestos y evidencia. La configuración de Google OAuth/OIDC, incluido el callback exacto y Google Cloud, está en [la guía de autenticación](docs/07_seguridad/08_google_oauth.md).

### Tarjetas de crédito

En `/app/cards` se pueden crear, editar y archivar tarjetas (banco, nombre, día de
cierre y vencimiento), registrar compras de uno o varios pagos y pagar cada cuota
desde una cuenta financiera activa. No se solicitan ni almacenan números de tarjeta
ni CVV. Administran tarjetas propietarios/administradores; los miembros pueden
registrar compras y pagos. Se conserva el hogar activo, CSRF, auditoría e idempotencia.

Las cuotas distribuyen centavos sin perder el total. Una compra en el día del cierre
entra en ese ciclo; después del cierre entra en el siguiente. El vencimiento siempre
es posterior al cierre; los días 29–31 se ajustan al último día disponible. El
calendario de cada compra queda fijo. Los gastos de tarjeta se incluyen en el resumen
por mes de vencimiento; `card_payment` descuenta el saldo de la cuenta sin duplicar
el gasto. Las cuotas con tarjeta se pagan completas; sin tarjeta se admiten abonos parciales.
Compras y pagos confirmados son inmutables.
Archivar una tarjeta impide nuevas compras y permite pagar las cuotas pendientes.

Aplicar las migraciones normales con `python backend/manage.py migrate`. No se
implementa ADR-002 ni se transforma el ledger existente a doble partida.

El panel financiero destaca el **saldo disponible actual** de efectivo, bancos y
billeteras activas, separado de ingresos, gastos y resultado del mes seleccionado.
La navegación anterior/siguiente y el selector de mes/año actualizan los totales
mensuales. La barra de gastos frente a ingresos identifica sobregasto. En cuentas
se puede seleccionar una cuenta y consultar entradas, salidas, ingresos, gastos y
el detalle de aperturas, transferencias y pagos de tarjeta del período. Los saldos
siguen siendo actuales al consultar otro mes.

### Compras sin tarjeta y gastos recurrentes

En `/app/installments` podés registrar una compra financiada sin tarjeta, con
acreedor opcional, primera cuota y frecuencia mensual; consultar pendientes y
pagar cuotas completas o parcialmente desde una cuenta existente. En
`/app/recurring` podés configurar suscripciones y otros gastos mensuales, cambiar
el importe de una ocurrencia pendiente, confirmar el pago y pausar, reanudar o
cancelar conservando el historial. Los vencimientos también aparecen en el panel.
Las recurrencias sólo generan gasto y descuentan saldo al confirmar su pago.
Las compras financiadas usan el criterio existente de gasto por vencimiento y sus
pagos no vuelven a contabilizar el gasto.

Aplicar las migraciones nuevas con `python backend/manage.py migrate`. No se
implementa ADR-002 ni una nueva arquitectura contable. Las cuotas con tarjeta
conservan sus pagos completos y los registros históricos existentes.

## Despliegue de producción

La [auditoría y guía de despliegue Fedora](docs/11_operaciones/01_despliegue_produccion.md)
describe las rutas `/srv/misgastos`, el entorno externo y los pasos manuales de actualización.
El VPS ejecuta únicamente el backend; Angular se compila y publica desde el equipo local.
