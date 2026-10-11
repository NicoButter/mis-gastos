# Gastio · Fase 2.0a — Auditoría de ADR-002 y viabilidad de migración

**Estado de ADR-002:** pendiente de ratificación y bloqueado para implementación hasta superar la prueba de migración aislada descrita aquí.  
**Fecha:** 2026-10-10  
**Alcance:** auditoría de código y diseño de migración. No se conectó a ninguna base de datos, no se modificó código financiero ni datos y no se ejecutaron pruebas.

## Decisión ejecutiva

El ledger actual es suficiente para los flujos líquidos de Fase 1 y sus saldos derivados; no es un diario de partida doble ni puede representar pasivos. Para incorporar tarjetas, préstamos u otras obligaciones sin libros financieros paralelos, se recomienda **C como estado objetivo**: migrar integralmente las operaciones y revisiones hacia un diario balanceado. La recomendación es condicionada, no una ratificación de ADR-002 ni autorización de ejecución.

La estrategia recomendada es una migración de expansión, backfill en esquema sombra, conciliación estricta, corte atómico de lectura/escritura y período de observación con el ledger original conservado en sólo lectura. No se habilitan escrituras independientes a dos libros. La prueba requerida tiene que resolver brechas de cobertura de auditoría y demostrar diferencia de ARS 0,00 por hogar, cuenta, período, categoría y tipo de movimiento. Hasta entonces ADR-002 permanece pendiente y tarjetas bloqueadas.

## 1. Auditoría del núcleo actual

La auditoría fue estática: se inspeccionaron los modelos, servicios, serializadores, consultas API, migraciones PostgreSQL y documentación de Fase 1.1. No se inspeccionaron filas ni credenciales.

### Estructura y semántica comprobadas

- `FinancialTransaction` es el objeto mutable de negocio: hogar, creador, tipo, importe positivo, ARS, fecha económica, cuenta origen, destino opcional, categoría, estado y número de revisión. Apertura, ingreso y gasto requieren una cuenta; transferencia añade destino y no lleva categoría.
- `LedgerEntry` es inmutable y referencia una cuenta líquida. Guarda un delta firmado por `transaction + revision + account`; no posee una cuenta contable de contrapartida. No registra deuda, patrimonio, ingreso o gasto en un diario general.
- Apertura crea una operación `opening` y una entrada positiva si el importe es mayor que cero. Hay una sola apertura por cuenta; apertura cero no crea operación. El saldo inicial no se modifica luego.
- Ingreso crea `+importe` en el activo líquido; gasto `−importe`; transferencia `−origen` y `+destino`. No hay saldo almacenado como campo; se deriva de entradas de operaciones posted cuya revisión coincide con la revisión vigente.
- Corrección actualiza el snapshot de `FinancialTransaction`, aumenta `revision` y agrega el juego completo de deltas de esa revisión. Las líneas anteriores siguen inmutables pero dejan de participar en saldo e informes. No son asientos de reversión acumulativos.
- Anulación cambia estado a `voided`, sin nueva revisión ni nuevos deltas. El selector excluye todas sus entradas; el historial y las filas previas permanecen. Por esto, no se debe migrar cada `LedgerEntry` histórica como efecto vigente independiente.
- `effective_date` define el período del dashboard y los filtros de fecha. `created_at`/`updated_at` y `AuditEvent.created_at` describen tiempo de registro/auditoría. Las transferencias y aperturas se excluyen de ingresos/gastos; transferencias tampoco cuentan en el neto de consumo.
- Las categorías se conservan como FK de la operación vigente. Los importes por categoría se calculan agrupando operaciones posted por período efectivo, categoría y tipo expense. Una categoría puede cambiar nombre/color/estado; identidad (slug/tipo) es estable. Los reportes actuales muestran el nombre actual para importes históricos.
- La escritura usa `transaction.atomic`, bloqueo de hogar y membresía, validación de relaciones dentro del tenant, `expected_revision` en correcciones, `WriteReceipt` único por hogar/actor/clave y fingerprint para repetición idéntica. El mismo hogar se serializa; hogares distintos pueden avanzar en paralelo.
- PostgreSQL impide borrado de operaciones y cambios/borrados de ledger, auditoría y recibos. Constraints comprueban forma, importe, ARS, estado, revisión y unicidad. Triggers diferidos validan al commit los signos/cantidades de entradas, totales de transferencia, correspondencia de referencias/moneda/tenant, revisión activa y evidencia de auditoría. Un trigger impide insertar entradas para una revisión histórica o anulada.
- Los selectores y endpoints limitan por hogar activo de sesión; servicios vuelven a resolver membresía. Las FKs cruzadas de cuenta/destino/categoría se comprueban en servicio y trigger PostgreSQL. Los UUID no son autorización.

### Invariantes que deben sobrevivir

1. Cada operación vigente corresponde exactamente a un único efecto económico vigente, cualquiera sea el número de revisiones. Las revisiones superadas son trazabilidad y compensaciones, no movimientos comerciales adicionales.
2. Saldo de cuenta líquida = saldo inicial + ingresos − gastos + transferencias entrantes − transferencias salientes, considerando operaciones posted actuales y moneda correspondiente. Las aperturas no son ingreso del período.
3. Por operación vigente, sumando sus cuentas líquidas, el delta coincide con su efecto neto anterior; las transferencias conservan el total de activos líquidos del hogar.
4. Dashboard: ingresos, gastos, neto, distribución por categoría, recuento y filtros temporales conservan su semántica y los valores históricos actuales. El pago de deuda no debe entrar como gasto de consumo.
5. Corrección/anulación es atómica, versionada, auditable, idempotente y no destruye líneas anteriores. Conflictos por revisión obsoleta siguen siendo 409.
6. Cada referencia financiera y cada posting pertenece al mismo hogar; ninguna consulta, agregado, detalle o recibo de un hogar puede incluir otro.
7. La fuente contable vigente debe ser única. Una proyección de compatibilidad sólo puede derivarse de esa fuente, nunca recibir escrituras independientes.

El balance de débitos/créditos es un invariante nuevo, adicional; no sustituye estos siete.

## 2. Alternativas para ADR-002

| Criterio | A. Ledger líquido + sublibro de pasivos | B. Diario sólo para operaciones nuevas | C. Migrar historia completa a diario balanceado |
|---|---|---|---|
| Consistencia contable | Dos representaciones relacionadas por convenciones; difícil probar conservación global | Dos semánticas según fecha de alta y potencialmente dos fuentes | Un modelo uniforme: por operación/moneda débitos = créditos |
| Complejidad de entrega | Inicialmente menor; conciliación compra/pago y reportes cruzados siguen permanentes | Media-alta: corte por cohortes, adaptadores y reportes híbridos | Alta y concentrada en migración/backfill; disminuye complejidad futura |
| Riesgo migratorio | No toca historia, pero legado y deuda nunca convergen | Riesgo de frontera, duplicación o discontinuidad al cruzar cohorte | Riesgo de reconstrucción y corte; controlable sólo con copia, reconciliación y rollback probado |
| Rendimiento | Consultas y dashboard agregan libros; riesgo de joins y agregados duplicados | Consultas condicionales a esquema/fecha y unión histórica/nueva | Agregaciones uniformes; volumen inicial de postings y plan de índices deben medirse |
| Compatibilidad de reportes | Adaptadores requeridos para sumar obligaciones y caja | Más difícil: reportes bifurcados entre legado y operaciones nuevas | API puede conservar DTOs y semántica con selectores compatibles; lectura debe validarse por paridad |
| Escalabilidad de dominio | Limitada: préstamo/ajuste/reembolso pide otro sublibro | Mejora parcial, dualidad persiste | Alta para activos, pasivos, patrimonio, ingresos y gastos; multidivisa sigue requiriendo FX explícito |
| Auditoría | Buen historial actual, pero eventos de deuda separados | Auditoría repartida y transición difícil de explicar | Reversiones/postings enlazados más snapshots de auditoría preservan linaje completo |
| Tarjetas/préstamos | Tarjetas posibles con integración artesanal; préstamos aumentan ramificaciones | Tarjetas nuevas en journal; deuda anterior en sublibro | Ambos entran como cuentas y operaciones balanceadas sin otro ledger |

**Evaluación:** A es opción razonable sólo si se aceptara que Gastio nunca ofrezca una vista contable uniforme. B es una transición tentadora, pero como estado operativo estable conserva dualidad, añade ramas en API/dashboard y no evita el backfill posterior. C ofrece el destino más verificable, a costa de una migración de riesgo mayor. Se recomienda C como destino con transición escalonada y gates; si el ensayo no demuestra reconstrucción o paridad completa, la decisión vuelve a revisión en vez de forzar el corte.

## 3. Modelo del diario propuesto

### Entidades conceptuales

- **ChartAccount / LedgerAccount:** plan de cuentas por hogar. Tipos `asset`, `liability`, `equity`, `income`, `expense`; código estable del sistema y etiqueta del hogar; moneda; estado; vínculo opcional y único a cuenta financiera o línea de crédito. No reutilizar una categoría como cuenta de mayor.
- **JournalEntry:** cabecera inmutable del evento contable: UUID, hogar, operación origen UUID/tipo, revisión fuente, fecha económica, fecha de registro UTC, fecha de creación, descripción no sensible, actor, estado y clave de agrupación. Único por operación origen/revisión/propósito. Las fechas económicas y de registro se mantienen separadas.
- **LedgerPosting:** línea inmutable: UUID, `JournalEntry`, secuencia, cuenta de mayor, débito, crédito, moneda, `FinancialAccount` o vínculo fuente cuando aplique, categoría opcional e identificador de origen. Exactamente una de débito/crédito es positiva; valores no negativos y precisión definida. Categoría es una dimensión analítica, no una cuenta de contrapartida.
- **FinancialTransaction / AuditEvent:** se conservan como API/linaje durante transición. Cada entrada del diario lleva referencia a transacción UUID y revisión; evento de auditoría conserva autor, snapshots y timestamp. No reemplazar UUID históricos.
- **Cuenta de mayor de activo monetario:** una por cuenta financiera y ARS. **Pasivo:** para línea/tarjeta o deuda a pagar. **Patrimonio:** al menos saldo inicial/apertura. **Ingreso/gasto:** cuentas de resultado por clase, con categoría como dimensión para mantener filtros. Códigos de control para diferencias no se usan como cuenta de “plug”; una diferencia detiene el proceso.

### Invariantes y enforcement

- Para cada `JournalEntry` y moneda: `SUM(debit) = SUM(credit)` y existe al menos dos líneas no nulas. No se puede expresar esto con un `CHECK` ordinario de una fila porque la suma abarca filas.
- Servicio de dominio crea cabecera y todas las líneas dentro de una transacción; valida referencia, moneda, hogar, revisión y sumas con Decimal. Bloquea la cabecera/hogar según orden de locks documentado, no permite modificar/eliminar líneas y sólo devuelve éxito después del commit.
- PostgreSQL debe hacer cumplir append-only con triggers; FKs y constraints validan cara única positiva, precisión, referencias y campos inmutables. Un **constraint trigger diferido** `AFTER INSERT/UPDATE/DELETE` por línea/cabecera reevalúa el grupo completo al commit y rechaza asiento sin postings o desbalanceado. Serializar cambios del asiento por lock de cabecera evita dos transacciones que validen cada una una mitad distinta. El rol de aplicación no puede deshabilitar triggers ni insertar por vías no autorizadas.
- Una alternativa más fuerte para cierre futuro es insertar postings sólo mediante una función PostgreSQL de posting que bloquea, agrega, valida y sella la cabecera; comparar operabilidad frente a trigger diferido antes de escoger. No asumir atomicidad de aplicación ni `CHECK` como garantía suficiente.
- Cada moneda se balancea separadamente. No sumar importes ARS y moneda extranjera en un mismo total sin postings FX explícitos, fuera de esta decisión.

### Correspondencia exacta de operaciones

| Origen | Débito | Crédito | Fecha económica / notas |
|---|---|---|---|
| Apertura positiva 100.000 | Activo monetario de cuenta +100.000 | Patrimonio / saldo inicial +100.000 | `effective_date`; apertura cero produce sin asiento, como hoy |
| Ingreso 25.000 | Activo monetario +25.000 | Ingreso, dimensión categoría +25.000 | `effective_date`; mantiene KPI income |
| Gasto 25.000 | Gasto, dimensión categoría +25.000 | Activo monetario +25.000 | `effective_date`; mantiene KPI expense |
| Transferencia 10.000 | Activo destino +10.000 | Activo origen +10.000 | Mismo evento y hogar; total activo neto cero; sin categoría ni P&L |
| Corrección de la revisión R a R+1 | Postings compensatorios inversos de R y postings de R+1 en el grupo de corrección | Espejo por cada línea/moneda | Revertir económicamente en la fecha original de R, con `recorded_at` de la corrección; registrar nuevo efecto con su nueva `effective_date`. Paridad de períodos incluye esta regla |
| Anulación de operación vigente | Reversión exacta de todas las líneas activas de su revisión | Contrapartida inversa línea a línea | Fecha económica original para neutralizar período histórico; fecha de registro de anulación para auditabilidad |
| Movimiento con fecha anterior | Igual que ingreso/gasto/transferencia | Contrapartida normal | Fecha efectiva anterior para KPIs, fecha de registro actual para orden de auditoría |
| Operación sobre cuenta archivada | No se permite nueva operación según regla vigente | — | Historial y saldos permanecen consultables. Reversión/compensación de evento previo puede usar la cuenta archivada, sin reactivarla |
| Idempotencia, misma clave y fingerprint | No crea líneas ni cabecera nueva; retorna recibo previo | — | Misma semántica 200/replay; otra carga con clave repetida, 409 |

Las cuentas pueden quedar negativas porque el producto actual permite gastar más
que el saldo. Para paridad, el backfill conserva el saldo firmado de la cuenta de
activo y no lo reclasifica automáticamente como préstamo/sobregiro; cualquier
reclasificación requiere un evento de ajuste explícito posterior.

Para R1→R2→R3, cada transición genera un grupo balanceado compensatorio y el nuevo efecto. Estado vigente es la suma de todos los postings hasta la última revisión no anulada. Al anular, se revierte el efecto vigente. El origen histórico se referencia siempre; no crear tres operaciones comerciales a partir de tres snapshots. La fecha económica de la compensación apunta al efecto que neutraliza, conservando los KPI actuales por mes; `recorded_at` expresa cuándo se conoció la corrección.

## 4. Revisiones: reconstrucción, evidencia y política

### Qué se puede reconstruir del diseño actual

`FinancialTransaction` contiene sólo la última versión; `LedgerEntry` conserva deltas inmutables por revisión y `AuditEvent` conserva snapshots antes/después. La guarda de PostgreSQL requiere evidencia de auditoría de revisión/estado al commit. En teoría, el evento `create` da R1; cada `update` contiene el snapshot previo y el posterior; un evento `void` marca la anulación. El actor y el tiempo de cada cambio se conservan en audit. Categoría, fecha efectiva, importe, cuenta/destino y descripción están en snapshots del modelo. Las aperturas no se corrigen; transferencias comparten la forma de revisión y ambas cuentas aparecen en la entrada.

Eso **no prueba aún** que todo registro histórico tenga una cadena completa: hace falta auditar cobertura real de AuditEvent, consistencia de `before/after`, orden de timestamps, disparadores de migración/despliegue, entradas sin auditoría, categorías FKs y el formato serializado de UUIDs/FKs. No se leyó la base en esta iteración. UUID común, snapshots repetidos y trigger actual son evidencia de diseño, no una conciliación de datos.

### Dos políticas posibles

1. **Reconstrucción integral de revisiones:** por operación ordenar auditorías de creación/revisión por `(created_at,id)`, validar continuidad R1…Rn, correspondencia de `before` con snapshot anterior, y delta de cada revisión. Insertar reversión + nuevo snapshot como postings con `source_transaction_id`, `source_revision`, `source_audit_event_id`; void revierte último efecto. Ventaja: conserva explicación financiera y fecha de registro de cada cambio. Costo: más postings, reglas de fechas históricas, datos incompletos detienen migración.
2. **Saldo contable inicial reconciliado + historia vinculada:** para cada operación usar sólo snapshot actual posted como movimiento inicial del journal y conservar todas las revisiones en AuditEvent/legado. Anuladas no generan saldo actual (o se representan por reversión de apertura si se necesita traza); crear saldos de apertura por cuenta con contrapartida de equity para cuadrar. Ventaja: backfill más simple. Consecuencia: no se puede consultar fácilmente el libro por fecha de registro, explicar cambios contables intermedios ni reconciliar ingresos/gastos de todos los períodos sólo desde el journal; auditar dependería del legado. El “saldo inicial” agregado puede esconder movimientos/categorías y no sirve si se requiere paridad mensual.

**Política recomendada para el objetivo de equivalencia histórica:** reconstruir todas las revisiones compensatoriamente cuando la cadena pasa validaciones; no convertir revisiones en operaciones nuevas ni crear diferencias de ajuste automáticas. Para una cadena incompleta, detener el hogar/lote y corregir la evidencia a partir de backups verificables o adoptar explícitamente política 2 con aprobación de producto y aceptación documentada de pérdida de granularidad. No imputar categoría genérica, inventar autor ni ocultar diferencia en equity. Las aperturas anuladas no existen por regla actual; una apertura se migra una vez, cuenta por cuenta.

## 5. Conciliación de viabilidad

### Ensayo aislado requerido

Crear snapshot temporal reproducible del origen con PII minimizada o fixtures sintéticos derivados del esquema, PostgreSQL compatible con producción y nombre/credenciales efímeros. Migrar a un esquema destino sombra. El proceso extrae sólo campos necesarios; informe contiene conteos y diferencias agregadas por hogar/cuenta/categoría/período, nunca nombres, emails, descripción, tokens, notas, claves de recibo ni credenciales. No apuntar a `gastio_db` ni a la base de desarrollo. Registrar versiones de código, migrations, timezone, hashes de entrada anonimizada/salida y parámetros.

Antes de materializar destino, ejecutar preflight read-only del origen en la copia:

- IDs y conteos; hogares, cuentas, categorías, operaciones, entradas por revisión, auditorías, recibos.
- Operaciones sin entrada/audit, diferencias de tenant/moneda/forma; filas `posted` sin entradas de revisión vigente y filas `voided` con historial coherente.
- Cada operación con eventos ordenados: continuidad de revisiones, campos mínimos, `before`/`after`, actor/timestamp, categoría y destino. Aperturas únicas y entradas no corregidas.
- Replay de `LedgerEntry` bajo la misma regla de selector vigente para reproducir saldo actual y transferencias neto cero.

### Matriz de paridad monetaria

Comparar origen (selector Fase 1) y destino (rollup del journal) para:

| Métrica | Clave de agrupación | Tolerancia |
|---|---|---|
| Saldo agregado | hogar, moneda | ARS 0,00 |
| Saldo | hogar, cuenta UUID, moneda | ARS 0,00 |
| Saldo de diario por cuenta de mayor | hogar, cuenta de mayor, moneda | igualdad exacta contra mapeo de activo y pasivos/patrimonio explicados |
| Ingresos/gastos/neto | hogar, mes de `effective_date`, moneda y tipo | ARS 0,00; exclusión de apertura/transferencia igual |
| Gasto por categoría | hogar, mes, categoría UUID | ARS 0,00; comparar UUID y no sólo label editable |
| Transferencias | hogar, mes, cuenta origen/destino | importe, cantidad y suma neta cero iguales |
| Aperturas | hogar, cuenta, fecha e importe | importe y cantidad iguales; fuera de KPI de ingreso |
| Anuladas/corregidas | hogar, estado, revisiones, tipo y período vigente | conteo/origen enlazado igual; el efecto anulado neto cero |
| Operaciones vigentes | hogar, tipo, estado, mes y total | conteo, sumas y UUIDs iguales |

La igualdad global no basta: el proceso hace `full outer join` de claves agregadas para que una métrica ausente también falle. Usa decimal exacto; no floats ni tolerancias porcentuales. Diferencia permitida de dinero: **0,00** en cada grupo aplicable. Los pasivos nuevos aún no existen en origen y se prueban aparte con fixtures contables balanceados, no se hacen pasar como paridad de Fase 1.

**Estado de viabilidad:** no se ejecutó el ensayo ni se leyó una copia en esta iteración. Por ello la estrategia de backfill está diseñada y es plausible, pero su viabilidad empírica **no está demostrada**; C no alcanza todavía criterios de aprobación. No se creó utilidad read-only: aún falta definir/validar el dataset aislado y esquema sombra, y un script sin esas entradas no demostraría nada. El siguiente incremento debe entregar el preflight/reconciliador independiente antes de cualquier migración de producción.

## 6. Seguridad, concurrencia, compatibilidad

| Garantía | Base de datos | Servicio/consulta |
|---|---|---|
| Balance por asiento/moneda | Constraint trigger diferido o función de posting transaccional; líneas append-only | Servicio agrupa todas las líneas en una `atomic`; decimal exacto; rollback ante fallo |
| Tenant en posting y relaciones | FK, unique compuesta y trigger que valida household en cada vínculo (incluidas cuenta/categoría/origen) | Resolver hogar desde membresía activa; cargar refs con queryset scoped; no confiar en ID cliente |
| Idempotencia | Unique `(household,actor,key)` | Mismo fingerprint devuelve receipt; distinto contenido 409; bloqueo hogar conserva orden actual |
| Revisión única/reversión | Unique `(source operation, source revision, purpose)`; postings inmutables | `expected_revision`, lock origen y hogar, reversión antes de reemplazo; audit evento atómico |
| Concurrencia | Locks/constraints impiden saldo aplicado duplicado; test de aislamiento PostgreSQL | Orden de locks hogar→membresía→origen/recibo; volver a validar pertenencia, estado y revisión |
| UUID/historial | FK PROTECT, referencias source UUID/revision/evento | Adaptadores conservan IDs API; exporte/import de auditoría verificado |

Multitenant debe validarse para UUID de hogar A consultados por miembro de A/B, cambio de hogar activo, FK de cuenta/categoría ajena, dashboard/listas y agregados. Los IDs en JSON de auditoría no son FK; un validador debe corroborar que el evento pertenece al mismo hogar y objeto. Reportes de migración no publican datos personales.

**Angular/API:** mantener endpoints, UUID, nombres snake_case, filtros, paginación, errores, idempotencia, `expected_revision` y DTOs actuales. Introducir un selector que lea journal y traduzca a `balance`, `income`, `expense`, `net`, `distribution`, `count`, `accounts` y `recent`. No cambiar semántica: `balance` sigue siendo total de activos líquidos, nunca activos menos deuda. Cuando se introduzca tarjeta, añadir campos separados (`liabilities`, `billed_due`, etc.) y rutas aditivas; no reinterpretar `expense` como pagos. Historial de operación debe enlazar asientos y eventos. Carga rápida no debe percibir cambio contable. OpenAPI se regenera y compara contractualmente antes/después; cambio incompatible requiere versión/adaptador explícito. No tocar componentes en esta iteración.

## 7. Etapas y recuperación

1. **Preparación:** congelar decisiones del plan de cuentas, fecha económica de reversiones, esquema de moneda y cobertura audit; inventario y backup probado. Baseline por hogar/cuenta/período anonimizado.
2. **Prueba aislada:** restaurar copia temporal no productiva y ejecutar preflight; construir esquema destino aditivo y backfill; reproducir desde cero para determinismo.
3. **Conciliación automática:** full outer join de todas las métricas de §5; validar constraints, referencias tenant, cero asiento desbalanceado y conteos UUID. Segundo operador revisa resumen agregado.
4. **Evaluación:** aprobar sólo si cero diferencias monetarias inexplicadas, auditoría completa o excepciones con política explícita, performance medida y contratos API compatibles. Fallo de cualquier gate detiene; no se generan ajustes “plug”.
5. **Preparación de transición:** en producción futura, ventana de mantenimiento, backup/restore ensayado, migration versionada y destino sombra cargado desde snapshot consistente. Registrar un watermark y bloquear temporalmente escrituras para evitar hueco entre snapshot y corte; esta decisión debe probarse bajo concurrencia.
6. **Verificación posterior:** comparar conteos/checksums y conciliación, ejecutar smoke/contract sobre DB segregada y observar lecturas por cohortes controladas. El ledger original permanece íntegro y de sólo lectura durante el período de observación; las lecturas del producto tienen una sola fuente seleccionada, no se suman ambos libros.
7. **Recuperación:** antes de habilitar escritura, revertir el selector al ledger original y descartar el esquema sombra. Tras habilitar nuevas operaciones, no hacer rollback destructivo ni reabrir escrituras en sistema antiguo: pausar escrituras financieras, recuperar backup/WAL o aplicar forward-fix con eventos compensatorios auditables. Restaurar backup implica recuperar snapshot completo y reproducir operaciones idempotentes posteriores, nunca borrar filas reales selectivamente.

No se hará doble escritura silenciosa. Una eventual fase de shadow-read compara resultados sin exponer agregado doble; escrituras sólo al sistema fuente activo. Si se necesitara replicación, debe ser outbox transaccional con consumidor idempotente y prueba de consistencia, no dos saves independientes.

## 8. Tarjetas: decisiones y límites

### Imprescindibles para el diario/migración

- Separar caja, deuda, patrimonio y resultado; asiento balanceado por moneda.
- Definir fechas `effective_date` y `recorded_at`; política de reversión que mantenga comparabilidad histórica.
- Enlazar operación/revisión/actor/audit y mantener idempotencia, aislamiento, atomicidad y compatibilidad DTO.
- Definir plan de cuentas, signo y forma de categorías; ARS primero. No dependen de calendario de emisor.

### Defaults recomendados para resolver antes de la feature

| Tema | Default inicial | Qué puede esperar |
|---|---|---|
| Cierre | Día de cierre 1–28; compra en fecha de cierre incluida en ciclo que cierra ese día; ciclo estimado hasta confirmación del emisor | Política por emisor y cierres especiales |
| Día 29/30/31 | Día objetivo se limita al último día calendario del mes (febrero incluido), sin arrastre bancario automático | Feriados y reglas particulares |
| Vencimiento | Desplazamiento entero de días desde cierre, configurado por línea, persistido en snapshot confirmado | Vencimientos variables por emisor; edición futura versionada |
| Compra próxima al cierre | La fecha económica de compra queda inalterada; período estimado sigue regla inclusiva; nunca se reescribe un resumen confirmado | Ajuste manual en caso de diferencia del emisor |
| Tarjetas adicionales | Pertenecen a una línea compartida; deuda/resumen a nivel línea, last4/alias opcionales; no guardar PAN/CVV/PIN | Límites por plástico y tokenización externa |
| Roles del hogar | Owner/admin administran línea/configuración y confirman resumen; members ven e ingresan gasto compartido; pago/reversión requiere owner/admin hasta ACL detallada; limited_entry denegado | Permiso por tarjeta/cuenta y compartir selectivamente |
| Archivada | No nuevas compras; deuda, resúmenes e historial visibles/pagables hasta saldo cero; archivado no borra ni bloquea abono/ajuste | Reabrir instrumento requiere evento auditado |
| Deuda preexistente | Alta mediante saldo inicial de pasivo + contra patrimonio/ajuste de apertura, detalle de cuotas remanentes como plan importado; no se cuenta como consumo del mes de alta | Importación automática desde emisor |

Estos defaults de producto no bloquean auditoría/backfill del ledger. Sí deben ratificarse antes de activar funciones que dependan de ellos. No incluir interés, mora, mínimo, cuotas con tasa o FX en la primera entrega.

## 9. Riesgos, bloqueantes y criterios de aceptación

### Bloqueantes actuales

- No hay evidencia empírica de restauración/backfill/conciliación en PostgreSQL temporal.
- Cobertura total de snapshots `AuditEvent` y cadena de revisiones no comprobada contra datos; no afirmar que reconstrucción histórica funciona hasta preflight.
- No está elegido formalmente entre historial completo reversible y saldo inicial con audit legado; se recomienda el primero sujeto a continuidad de cadena.
- Falta prototipo/proof del trigger diferido balanceado bajo inserciones concurrentes y política de locks; `CHECK` simple no basta.
- Paridad por período y categoría/UUID, incluyendo correcciones con cambio de fecha/categoría y anulaciones, no se ha medido.
- Umbral de rendimiento del nuevo rollup y compatibilidad contractual deben compararse con benchmark base antes del corte.

### Aceptación verificable para ratificar ADR-002

1. Alternativas A/B/C evaluadas y C aprobada explícitamente con las limitaciones de backfill.
2. Tabla de plan de cuentas, signos y postings para las siete clases de operación de §3 aceptada.
3. Constraints/triggers reales prueban asiento vacío, desbalance, moneda mixta, tenant cruzado, edición/borrado y doble escritor concurrente; ninguna corrida deja commit parcial.
4. Fixture reproducible de creación, dos correcciones, cambio de categoría/fecha, anulación, transferencia y apertura genera chain completo y neto exacto; revisiones no se cuentan como operaciones separadas.
5. Copia temporal aislada ejecuta preflight + backfill desde cero; conciliación por cada clave de §5 da diferencias ARS 0,00 y conteos/UUID iguales; reporte no contiene PII/secrets.
6. Caso de cadena incompleta interrumpe migration sin escrituras parciales y entrega sólo errores agregados con referencias seguras.
7. Aislamiento hogares A/B, miembro multi-hogar, permisos, idempotencia y concurrencia verificados sobre PostgreSQL aislado.
8. API/OpenAPI y Angular mantienen contratos/semántica preexistentes; pruebas de contrato y smoke demuestran paridad.
9. Backup/restore, ventana de cutover, selector reversible antes de escrituras nuevas y recuperación forward-fix tras corte se ensayan.
10. No se elimina el ledger original hasta decisión posterior, período acordado de observación y backup verificable.

## 10. Incrementos propuestos

- **2.0a.1 — Evidencia de origen:** preflight read-only, cobertura AuditEvent, inventario agregado y fixture de cadenas de revisiones; sin esquema nuevo.
- **2.0a.2 — Prototipo aislado:** esquema sombra JournalEntry/LedgerPosting, guards PostgreSQL, importador repetible y reconciliador. Sólo fixture/snapshot temporal, sin componentes Angular ni producción.
- **Gate ADR-002:** revisión técnica de output anonimizado y aceptación de diferencias cero; ratificar/rechazar C. Si falla, evaluar explícitamente A o pérdida de granularidad bajo política 2.
- **2.1 — Fundamento productivo:** esquema aditivo, backfill/cutover ensayado y adaptadores compatibles; aún no tarjetas hasta estabilidad observada.
- **2.2 — Tarjetas y compras:** línea/plásticos, compras/cuotas y resúmenes con asientos balanceados.
- **2.3 — Aplicaciones/pagos:** pago parcial/total, deuda pendiente, devolución/ajustes y dashboard de deuda separado.

No iniciar 2.1 antes del Gate ADR-002. Las implementaciones financieras mantienen su suite aislada y nunca ejecutan contra `gastio_db`.

## Fuentes de repositorio

- `backend/apps/transactions/models.py`, `services.py`, `views.py`, `serializers.py`.
- `backend/apps/transactions/migrations/0003_ledger_guards.py`, `0004_opening_and_revision_seal.py`.
- `backend/apps/wallets/models.py`, `backend/apps/categories/models.py`, `backend/apps/audit/models.py`.
- `docs/10_planificacion/11_nucleo_financiero.md`, `13_diseno_fase_2_tarjetas_cuotas.md`.

Esta auditoría amplía la recomendación de Fase 2.0; prevalece como gate de viabilidad y deja ADR-002 **pendiente**, no aprobado.

### Seguimiento Fase 2.0b

Se implementó el POC aislado y pasaron 11 escenarios sintéticos sobre PostgreSQL
18.6. El resultado valida constraints, reejecución, rollback y agregados para los
fixtures. No se pudo evaluar el historial de desarrollo: el endpoint PostgreSQL
local no respondió y no se usó `gastio_db`. Por lo tanto, continúa bloqueada la
ratificación hasta el PASS de copia real. Detalle: [prueba de migración 2.0b](15_prueba_migracion_contable.md).
