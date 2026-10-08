# 02 · ERS — Especificación de Requisitos de Software

**Versión:** 0.1 · **Estado:** propuesta para aprobación · **Ámbito:** Gastio MVP

## 1. Introducción

Este documento define requisitos de usuario (RU), funcionales (RF), no funcionales (RNF), de sistema (RS), reglas de negocio (RN), restricciones y criterios de aceptación para un SaaS multitenant de finanzas familiares.

## 2. Requisitos de usuario

| ID | Necesidad del usuario | Prioridad | Verificación |
|---|---|---|---|
| RU-01 | Crear un hogar y colaborar con integrantes | Must | Alta e invitación efectivas |
| RU-02 | Registrar un gasto en pocos pasos desde celular | Must | Completar con 3 campos, sin navegación innecesaria |
| RU-03 | Conocer ingresos, gastos y balance de un período | Must | Dashboard concilia con libro de movimientos |
| RU-04 | Consultar y corregir movimientos | Must | Edición/auditoría visibles según rol |
| RU-05 | Separar efectivo, bancos, billeteras y tarjetas | Must | Saldos y obligaciones diferenciados |
| RU-06 | Ver cuotas y obligaciones por mes futuro | Must | Calendario consistente con plan de cuotas |
| RU-07 | Definir un presupuesto y saber cuánto resta | Must | Cálculo reproducible por categoría |
| RU-08 | Administrar pertenencia y acceso al hogar | Must | Invitación, revocación y cambio de hogar |
| RU-09 | Revisar gastos pendientes al terminar el día | Should | Cierre optativo sin bloqueo posterior |
| RU-10 | Exportar movimientos e informes | Should | Archivo coincide con filtros |
| RU-11 | Trabajar sin conectividad | Could | Cola y resolución de conflictos (futuro) |

## 3. Requisitos funcionales

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-001 | Registrar usuario e iniciar/cerrar sesión | Must | Sesión segura, cierre invalida credenciales aplicables |
| RF-002 | Crear/renombrar hogar | Must | Un creador queda titular; slug o UUID no expone otro hogar |
| RF-003 | Invitar miembros y aceptar/rechazar invitaciones | Must | Invitación limitada y no reutilizable después de aceptar |
| RF-004 | Asignar titular, administrador, miembro o carga limitada | Must | Permisos comprobados en API por operación y objeto |
| RF-005 | Seleccionar hogar activo | Must | Contexto explícito en rutas/API; no confiar solo en frontend |
| RF-006 | Crear/editar/archivar cuentas manuales | Must | Cuenta archivada conserva historial, no acepta nuevos movimientos |
| RF-007 | Crear/editar/archivar categorías por hogar | Must | No eliminar categoría referenciada; sin cruces entre hogares |
| RF-008 | Crear ingresos y gastos con monto positivo, moneda, fecha, cuenta, categoría y nota opcional | Must | API valida monto, fecha, pertenencia y campos requeridos |
| RF-009 | Crear transferencia entre cuentas del mismo hogar | Must | Un único evento contable mueve fondos sin generar ingreso/gasto |
| RF-010 | Listar/buscar/filtrar/paginar movimientos | Must | Filtros combinables por fecha, categoría, cuenta, tipo y texto |
| RF-011 | Editar o anular movimientos sin perder trazabilidad | Must | Saldo se recalcula y auditoría registra actor y cambio |
| RF-012 | Configurar tarjeta (cierre, vencimiento, cuenta de pago) | Must | Ciclo visible y validación de días aplicables por mes |
| RF-013 | Registrar compra con tarjeta y cuotas | Must | Plan de cuotas suma total, política de redondeo explícita |
| RF-014 | Registrar pago de tarjeta vinculado a cuenta de fondos | Must | Disminuye fondos/deuda sin duplicar gasto de consumo |
| RF-015 | Mostrar cuotas y vencimientos futuros | Must | Total mensual corresponde a cuotas programadas |
| RF-016 | Definir presupuesto mensual por categoría | Must | Aviso visual de uso y monto restante, sin bloquear gasto |
| RF-017 | Mostrar KPIs y gráficos del período | Must | Totales de gasto excluyen transferencias y pagos de resumen |
| RF-018 | Ofrecer flujo rápido móvil con valores sugeridos | Must | Monto/categoría/cuenta; confirmación y prevención de doble envío |
| RF-019 | Mostrar estados vacíos, carga, éxito y error | Must | UI accesible y usable en móvil |
| RF-020 | Auditar cambios financieros y permisos | Must | Historial solo para autorizados; trazas no exponen secretos |
| RF-021 | Permitir gastos recurrentes y confirmación de ocurrencias | Should | No duplicar instancias al reintentar tareas |
| RF-022 | Permitir objetivos de ahorro | Should | Progreso ligado a aportes reales designados |
| RF-023 | Cierre diario opcional por miembro/hogar | Should | Puede reabrirse; sin pérdida de registros |
| RF-024 | Exportar CSV/PDF de movimientos/reportes | Should | Respetar tenant y filtros |
| RF-025 | Alertas de presupuesto y vencimientos | Should | Preferencias por usuario y sin spam |
| RF-026 | Suscripciones SaaS, cupos y facturación | Could | Solo fases comercializadas; no implementarlo en MVP |

## 4. Requisitos no funcionales

| ID | Dimensión | Criterio comprobable MVP |
|---|---|---|
| RNF-001 | Aislamiento | Pruebas de acceso cruzado dan 403/404 sin filtrar datos |
| RNF-002 | Seguridad | TLS en producción; protección CSRF según esquema auth; cookies seguras; control de acceso server-side |
| RNF-003 | Rendimiento | Objetivo p95 de endpoints de carga/listado < 500 ms con datos de prueba definidos, excluida red; revisar en piloto |
| RNF-004 | Móvil | Flujo de carga desde 360 px sin desbordes horizontales |
| RNF-005 | Accesibilidad | WCAG 2.2 AA como objetivo; teclado, contraste, labels, focus |
| RNF-006 | Integridad | Transacciones atómicas; idempotencia de creación; importes decimales |
| RNF-007 | Trazabilidad | Log de auditoría de cambios críticos con actor/fecha/objeto |
| RNF-008 | Disponibilidad | Objetivo operativo inicial 99.5% mensual, no garantía contractual MVP |
| RNF-009 | Recuperación | Copias diarias cifradas, restauración verificada; metas iniciales RPO 24 h / RTO 8 h sujetas a infraestructura |
| RNF-010 | Privacidad | Minimización, política de retención, exportación y eliminación administrada |
| RNF-011 | Mantenibilidad | Apps por dominio; CI con tests/lint/format; migraciones versionadas |
| RNF-012 | Observabilidad | Logs estructurados, health checks y métricas sin contenido financiero sensible |
| RNF-013 | Compatibilidad | Últimas 2 versiones principales de navegadores modernos; responsive PWA online |
| RNF-014 | Localización | Interfaz es-AR, formatos de moneda y fecha por configuración |
| RNF-015 | Escalabilidad | Índices compuestos por hogar/fecha y paginación; medición antes de escalar |

## 5. Requisitos del sistema y restricciones técnicas

| ID | Definición | Validación |
|---|---|---|
| RS-001 | Un único repositorio, monolito modular backend | Árbol de módulos y un despliegue backend principal |
| RS-002 | Backend Python Django + DRF | Pruebas API y migraciones reproducibles |
| RS-003 | Frontend Angular + Tailwind | Build reproducible y PWA instalable |
| RS-004 | PostgreSQL como almacenamiento principal | Configuración por variables, sin SQLite como producción |
| RS-005 | Clave de tenant obligatoria en entidades del hogar | Constraints y pruebas cruzadas |
| RS-006 | Usuario puede pertenecer a N hogares | Membership N:M con unicidad por pareja |
| RS-007 | Moneda representada con código ISO y Decimal | Redondeo/documentación de precisión |
| RS-008 | Entorno dev reproducible y `.env.example` sin secretos | Arranque documentado sin credenciales en repo |
| RS-009 | Preparar workers Celery/Redis para tareas posteriores | No hacer depender MVP de cola si no se necesita |
| RS-010 | Despliegue apto para Fedora/Nginx/Gunicorn | Health, estáticos, migraciones, HTTPS |
| RS-011 | Contrato REST `/api/v1/` estable y versionado | OpenAPI y tests de contrato |
| RS-012 | CI ejecuta backend/frontend tests, lint, migración check | Pipeline verde antes de merge |

## 6. Reglas de negocio

| ID | Regla |
|---|---|
| RN-001 | Todos los montos de captura son positivos; el tipo define el efecto contable. |
| RN-002 | Transferencia de A a B no es ingreso ni gasto; A y B deben pertenecer al mismo hogar y tener moneda compatible en MVP. |
| RN-003 | Gasto con tarjeta reconoce consumo una vez, al comprar; el pago posterior solo cancela deuda y reduce fondos. |
| RN-004 | Para cuotas, el total asignado debe igualar el importe total original; diferencia de centavos se asigna determinísticamente a la última cuota. |
| RN-005 | No se suman ARS y USD sin conversión explícita definida y registrada. |
| RN-006 | Cada movimiento posee autor, hogar, fecha efectiva y timestamps técnicos. |
| RN-007 | Las modificaciones críticas generan registro de auditoría; anular no implica borrar físicamente transacciones. |
| RN-008 | El presupuesto observa gastos de consumo del período, no transferencias ni pagos de tarjetas. |
| RN-009 | Un usuario sin membresía activa no puede leer datos del hogar, aunque conozca un ID. |
| RN-010 | Titular no puede dejar el hogar sin transferir titularidad a otro usuario autorizado. |

## 7. Interfaces externas y datos

UI web/PWA (es-AR); API JSON HTTPS; autenticación basada en sesión segura o mecanismos equivalentes documentados; OAuth Google opcional si la configuración está disponible; PostgreSQL. Sin conexiones bancarias en MVP.

## 8. Matriz de trazabilidad inicial

| Objetivo | Requisitos | Casos de uso | Pruebas |
|---|---|---|---|
| Carga rápida | RU-02, RF-008, RF-018 | CU-05 | T-05, T-06 |
| Colaboración segura | RU-01, RU-08, RF-002..005 | CU-01..04 | T-01..04 |
| Balance confiable | RU-03, RF-009, RF-014, RF-017 | CU-06, CU-10 | T-07..10 |
| Tarjetas y cuotas | RU-06, RF-012..015 | CU-08..10 | T-09..12 |
| Presupuesto | RU-07, RF-016 | CU-11 | T-13 |

## 9. Criterio de aprobación MVP

MVP aceptado si cada requisito Must funciona de extremo a extremo, las pruebas de aislamiento pasan, el cálculo contable es reproducible, la interfaz móvil pasa accesibilidad base y el deploy staging puede reproducirse siguiendo README.
