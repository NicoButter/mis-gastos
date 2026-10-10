# Gastio — Fase 1.1: estabilización del núcleo financiero

Fecha: 2026-10-10. Alcance: auditoría, regresiones, integración E2E, UX móvil y
medición del núcleo de Fase 1. No se agregaron tarjetas, cuotas, presupuestos, IA,
permisos privados ni funciones comerciales. No se realizaron commits ni pushes.

## Resultado y recomendación

El modelo de revisiones contables existente se conserva: no se detectaron impactos
duplicados al corregir, anular o reintentar. Se corrigieron defectos de restauración
de sesión, validación de entradas, orden de paginación y estado de interfaz.
Playwright conecta Angular con Django y PostgreSQL reales usando sesiones de test.

Se recomienda iniciar el diseño de Fase 2 sobre este núcleo, conservando las
regresiones y definiendo antes de implementar tarjetas/cuotas las reglas de fecha
económica, pago y reconocimiento de gastos. Esta validación no habilita por sí sola
un lanzamiento a producción: quedan las comprobaciones físicas de móvil y las
limitaciones de permisos detalladas abajo.

## Defectos encontrados y correcciones

| Hallazgo | Impacto | Corrección y evidencia |
|---|---|---|
| Navegación inicial bloqueante ejecutada en paralelo al initializer de sesión | Un acceso directo a `/app` con cookie válida terminaba en login aunque `/auth/me/` respondía 200 | Navegación inicial predeterminada después de los initializers. E2E entra directamente a `/app`, demorando la identidad 200 ms; también comprueba visitante sin cookies |
| Creación/selección de hogar usaban `.get()` sobre cualquier JSON | Arrays y strings provocaban 500 | Se usan los serializers declarados en OpenAPI. Seis regresiones de cuerpo incorrecto/missing fields esperan 400, sin crear hogares |
| Querysets agregados de cuentas/categorías sin orden explícito | Warning de paginación; no había garantía explícita de recorrido estable | Orden por nombre/UUID en cuentas, tipo/nombre/UUID en categorías; regresión de 30 cuentas con nombres idénticos, tres páginas sin pérdidas ni duplicados |
| Finalización tardía de una escritura podía cerrar/limpiar un formulario de otro hogar | Pérdida del borrador y confirmación incorrecta después de cambiar el hogar | Se verifica el hogar capturado antes de aplicar éxito/error. Regresiones de cuenta y carga rápida con promesas pendientes |
| Historial pendiente podía agregarse a otro movimiento/hogar; errores de opciones podían sobrevivir al cambio | Evidencia de interfaz mezclada o errores obsoletos | Versión de solicitud para historial, verificación del hogar, avance de página sólo tras éxito; invalidación de solicitudes de listado/dashboard al limpiar contexto |
| Campos de operación editables durante el envío | El usuario podía cambiar selecciones mientras se conservaba el payload anterior | Fieldset deshabilitado, estado `aria-busy`, rechazo de opciones obsoletas y bloqueo de envío durante carga. Test de doble envío y reintento |
| Menú móvil permanecía abierto al navegar; pie de usuario con posición absoluta | Ocultaba el módulo seleccionado; riesgo de superposición en pantallas bajas | Cierre al navegar, sidebar desplazable y usuario en flujo normal |
| Algunos targets táctiles tenían menos de 44 px; importe rápido heredaba `text-base` de `.form-input` | Menor facilidad de interacción y de lectura | Targets de navegación/acciones financieras ≥44 px, importe de 30 px, márgenes de scroll y espacio inferior para barra móvil/safe area |
| Categorías sin indicador de carga/estado vacío | Pantalla aparentemente sin respuesta | Estado `role=status` y mensaje vacío |
| Configuración de test aceptaba cualquier `DATABASE_TEST_NAME` | Una configuración errónea podía apuntar el runner a una base real | Prefijo obligatorio `gastio_test`, rechazo del nombre fuente, charset UTF-8 con template0; regresión de rechazo de nombres reales |

No se modificó el motor de asiento/revisión ni se introdujeron migraciones.
Las aperturas siguen siendo no negativas e inmutables; los saldos posteriores
pueden ser negativos. Correcciones en cuentas/categorías archivadas siguen
requiriendo reactivar o elegir referencias activas; las anulaciones permanecen
posibles sin reactivar. Se conserva esta política actual, sin ampliar el alcance.

## Auditoría funcional y seguridad

Se revisaron servicios, serializers, viewsets, modelos, constraints/triggers,
autenticación, tenant, componentes Angular y documentación de Fase 1.

- Cuentas: apertura cero sin asiento; apertura positiva separada de ingresos;
  archivado conserva saldo e historial y bloquea nuevas operaciones; no hay DELETE.
- Categorías: 18 iniciales por hogar; seed idempotente; altas propias, slug/tipo
  estables, inactividad bloquea uso; agregaciones y filtros están acotados al hogar.
- Ingresos/gastos: precisión de dos decimales, importe positivo, fecha válida,
  referencias activas y moneda ARS. La validación no confía en selecciones de Angular.
- Transferencias: dos entradas por revisión, distintas cuentas del mismo hogar y
  moneda; el consolidado no cambia y no se computan como ingreso/gasto.
- Correcciones: revisión nueva completa; entradas anteriores inmutables no suman.
  La regresión mueve un gasto entre cuentas y reintenta la corrección con la misma
  clave: el origen recupera su saldo y sólo el destino recibe el impacto nuevo.
- Anulaciones: `voided` excluye todas las revisiones del saldo; la repetición con
  la misma clave devuelve el recibo; otra clave o corrección posterior obtiene 409.
  Se verifica exactamente una alta, una corrección y una anulación en auditoría.
- Concurrencia: escrituras idénticas paralelas producen un asiento; corrección y
  anulación simultáneas con revisión 1 permiten una sola mutación. El bloqueo del
  hogar y la revalidación/bloqueo de membresía siguen en vigencia.
- Dashboard: saldo actual incluye archivadas; KPIs y recientes pertenecen al mes
  seleccionado. Aperturas/transferencias no inflan ingresos/gastos. Se refresca al
  volver desde otros módulos y ante la señal de cambios.
- Tenant: selección desde sesión validada por servidor. `X-Household-ID` sólo
  detecta contexto desactualizado (409), nunca concede acceso. Se prueban usuarios
  separados, un usuario multi-hogar, UUIDs ajenos, destino/categoría cruzados,
  listas, detalle, historial, escritura, dashboard y revocación. Los triggers
  rechazan referencias de otro hogar incluso fuera de la API.
- Autenticación: cookies/sesión/CSRF reales; suites sin Google. Una mutación sin
  CSRF se rechaza. Producción no incorpora rutas de login de prueba ni flags de bypass.

| Rol | Lectura financiera compartida | Crear operaciones | Corregir/anular | Administrar cuentas/categorías |
|---|---|---|---|---|
| owner/admin | Todo su hogar activo | Sí | Cualquier movimiento mutable del hogar | Sí |
| member | Todo su hogar activo | Sí | Sólo los propios | No |
| limited_entry | No (403) | No en estos endpoints | No | No |
| No miembro/revocado | No (404); anónimo 403 | No | No | No |

**ACL por cuenta pendiente:** no existe visibilidad privada ni asignación individual.
Todas las cuentas implementadas son compartidas del hogar. Antes de habilitar
cuentas privadas/carga limitada hay que agregar ACL y filtrar listas, movimientos,
auditoría y agregaciones para evitar inferencias mediante totales. El permiso
conceptual `transaction.create` de `limited_entry` no habilita esta API: el servicio
financiero lo rechaza explícitamente.

## E2E reproducible y protección de datos

`frontend/playwright.config.ts` usa Chromium en tres proyectos: escritorio
1280×800, móvil táctil 360×740 y 390×844. Una ejecución crea una base aleatoria
`gastio_test_e2e_<uuid>` con migraciones y un hogar/usuario por proyecto.
`backend/tests/e2e_server.py` usa `Client.force_login()` fuera de los endpoints,
genera cookies en `frontend/e2e/.auth/` con permisos 0600 y sirve el WSGI real en
loopback. Las cookies están excluidas de Git y se eliminan al cerrar el runner.
Playwright cierra los servidores con SIGTERM y permite 10 segundos para limpiar.
Si el proceso recibe SIGKILL o la máquina se apaga, puede quedar una base de test
huérfana: revisar y retirar exclusivamente el UUID de esa ejecución en el clúster
de pruebas. Nunca ejecutar `flush` ni limpieza masiva de bases del servidor real.

Se sigue el mecanismo de cookies mediante
[storageState de Playwright](https://playwright.dev/docs/auth). No se falsifican
respuestas financieras: el único mock de error HTTP afecta al dashboard para
verificar su estado de error. Para probar respuesta perdida se envía primero la
operación a Django con `route.fetch()`, se corta la respuesta al navegador y luego
se reintenta con la misma clave. Se comprueba el saldo exacto y que el doble click
no inicia otra solicitud.

Los escenarios cubren sesión al acceso directo, visitante, cuentas y apertura,
ingreso, gasto, transferencia, corrección, anulación, historial, dashboard/saldos,
navegación, carga rápida, importe inválido, estado sin cuentas, respuesta perdida,
error de servidor y desbordamiento horizontal. Las capturas `quick.png` y el reporte
HTML se generan en `frontend/test-results`/`frontend/playwright-report`; las trazas
se conservan sólo ante fallo y pueden contener cookies/datos sintéticos. No publicar
esos artefactos como contenido público.

Requisitos: dependencias backend instaladas en `.venv`, `npm ci`, PostgreSQL exclusivo
para pruebas con rol que pueda crear bases y puertos 8001/4201 libres. No cargar `.env`
de producción. Ejemplo para un clúster local de pruebas en 55432:

```bash
export DATABASE_URL='postgresql://USUARIO_TEST@127.0.0.1:55432/postgres'
export DJANGO_SECRET_KEY='solo-test'
export PLAYWRIGHT_BROWSERS_PATH=/tmp/gastio-playwright
npm --prefix frontend ci
cd frontend
npx playwright install chromium
npm run e2e
```

El runner no reutiliza servidores existentes, para evitar apuntar accidentalmente
al backend real. La nueva tarea CI E2E utiliza PostgreSQL 17 dentro de un contenedor
independiente. También se añadieron Django check y validación OpenAPI al job backend.
La configuración CI está preparada; no se ejecutó en GitHub porque no hubo push.

## Rendimiento medido

Medición reproducible en `backend/tests/test_finance_performance.py`, opt-in con
`GASTIO_BENCHMARK=1`, únicamente dentro de la DB de pytest. Dataset determinista:
un hogar, una cuenta, una categoría usada, gastos de 1,25 ARS distribuidos en 28
fechas de octubre, primero 100 y luego 10.000 movimientos. Se generan ledger y
auditoría, se ejecutan los triggers y `ANALYZE` en las tablas sintéticas.

Cada endpoint se calienta una vez y se mide 20 veces con `APIClient` y
`CaptureQueriesContext`. Incluye autorización, consultas y serialización Django,
no latencia de red/navegador. p95 es el percentil empírico por rango (muestra 19/20).
No se fijan presupuestos temporales dependientes de hardware; la regresión exige
que el número de consultas no crezca con el volumen.

| Endpoint | Consultas, ambos volúmenes | Mediana / p95 a 100 (ms) | Mediana / p95 a 10.000 (ms) |
|---|---:|---:|---:|
| Movimientos (25 por página) | 5 | 8,46 / 11,92 | 9,73 / 10,59 |
| Cuentas y saldos | 5 | 5,84 / 8,28 | 12,52 / 15,51 |
| Dashboard | 12 | 11,71 / 20,49 | 23,24 / 27,07 |
| Filtro fecha + categoría | 5 | 9,30 / 13,87 | 10,50 / 20,58 |

[Evidencia JSON con EXPLAIN ANALYZE/BUFFERS](../09_calidad/evidencias/fase11-performance.json).
Los planes usan el índice existente hogar/fecha/id e incremental sort para el
listado y filtro; el saldo agrega el ledger y consulta la revisión vigente.
No hay N+1 observado. El dashboard tiene consultas separadas para total de importes,
count, distribución, cuentas y recientes; no se cambian sin evidencia de cuello de
botella. No se agregaron índices ni caché.

Limitaciones: datos homogéneos, caché caliente, PostgreSQL local 18.6 y ejecuciones
con otras verificaciones en la máquina. Las cifras no son un SLA ni una prueba de
carga. Falta medir muchos hogares/cuentas/categorías, revisiones acumuladas,
páginas profundas, filtros de búsqueda, p95 bajo usuarios concurrentes y contención
del bloqueo del dashboard. Repetir en PostgreSQL 17/infra de destino antes del piloto.

```bash
GASTIO_BENCHMARK=1 .venv/bin/python -m pytest -c backend/pyproject.toml \
  backend/tests/test_finance_performance.py -q -s
```

Salida por defecto: `/tmp/gastio-phase11-benchmark.json`. Puede cambiarse con
`GASTIO_BENCHMARK_OUTPUT`. Pytest crea/elimina `gastio_test`; no usa `gastio_db`.

## Validación y límites de cierre

| Verificación | Resultado |
|---|---|
| Backend PostgreSQL | 58 aprobadas, 1 benchmark omitido por opt-in |
| Benchmark opt-in | Aprobado, mediciones y planes conservados en JSON |
| Frontend Angular | 23 aprobadas en 4 archivos |
| Playwright | 6 aprobadas, 23 segundos; escritorio + 360/390 px |
| Django check / migraciones pendientes | Sin problemas / ninguna |
| Ruff / Black | Aprobados |
| TypeScript lint / build producción | Aprobados; bundle inicial 343,67 kB |
| OpenAPI | Válido con --validate --fail-on-warn |
| CI YAML | Válido; ejecución GitHub pendiente |

Los resultados también se registran en el estado de implementación. Se ejecutaron pytest contra PostgreSQL temporal, pruebas Angular, Ruff,
Black, Django check, detección de migraciones, lint TypeScript (incluido E2E), build
de Angular y `spectacular --validate --fail-on-warn`.

El clúster exclusivo de esta auditoría está en `/tmp/gastio-phase11-pg`, puerto 55432;
no se leyó `.env`, no se conectó a `gastio_db`, no se borraron registros reales ni se
aplicaron migraciones a bases reales. Al cierre se verificaron cero bases de test
remanentes, se eliminaron las cookies E2E y se detuvo el clúster temporal. Las restricciones de sockets/procesos del
sandbox se resolvieron con autorización para ejecutar pruebas fuera del sandbox.
Chromium requirió el binario alternativo Ubuntu de Playwright para Fedora.

Pendientes conocidos:

- Teclado numérico real, scroll con teclado abierto, uso con una mano y safe area
  de iOS/Android físicos. La emulación valida `inputmode=decimal`, targets y layout;
  no afirma ergonomía física ni certificación WCAG. Quick requiere desplazamiento
  vertical cuando hay muchas categorías; no se rediseñó la identidad.
- WebKit/Firefox y OAuth con Google real quedan fuera de la suite; el flujo OAuth
  requiere validación externa propia. La sesión y CSRF sí usan infraestructura real.
- ACL por cuenta y carga limitada, según tabla de permisos; no habilitar su acceso
  antes de implementar filtrado completo de agregaciones.
- Aperturas negativas no soportadas por la política vigente; corrección de aperturas
  no disponible. No convertir una apertura en ingreso ni editar ledger para ajustarla.
- Bloqueo por hogar también en dashboard, retención ilimitada de recibos/auditoría
  y crecimiento del ledger por revisiones: observar en piloto antes de optimizar.
- Deprecación interna de drf-spectacular con Python 3.14; no genera fallos de contrato.
- CI nueva aún sin ejecución remota. PostgreSQL 17 queda como verificación de destino.
