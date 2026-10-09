# 09 · Estrategia de calidad y aceptación

## Pirámide

- Unitarios: importes/contabilidad, cuotas/ciclos, permisos y presupuestos.
- Integración: API + PostgreSQL real de pruebas, transacciones, FKs cruzadas, idempotencia.
- E2E: onboarding, gasto rápido, tarjeta/cuotas/pago, navegación responsive y roles.
- Seguridad: pruebas de acceso entre al menos dos hogares y usuarios multi-membresía.
- Rendimiento: p95 objetivo RNF-003 con semilla reproducible y metodología documentada.

## Catálogo de pruebas mínimo

| ID | Escenario | Resultado esperado |
|---|---|---|
| T-01 | Miembro A lee/lista/busca gastos B | Nunca devuelve recursos B |
| T-02 | Gasto A con cuenta o categoría B | 400/403/404; sin persistencia |
| T-03 | Miembro sin permiso intenta alterar rol | Rechazo y auditoría apropiada |
| T-04 | Reusar token invitación | No crea dos membresías |
| T-05 | Gasto móvil válido | 201 y saldo/presupuesto correctos |
| T-06 | Reintentos concurrentes con misma clave | Un solo movimiento financiero |
| T-07 | Transferencia interna de $100 | Patrimonio neto consolidado inalterado |
| T-08 | Anular gasto | Reversión consistente, historial preservado |
| T-09 | Compra 100.00 en 3 cuotas | Cuotas suman exactamente 100.00 |
| T-10 | Pagar resumen de compra ya reconocida | Gasto de consumo no se duplica |
| T-11 | Cierre día 31 / vencimiento mes corto | Regla de calendario aplicada consistentemente |
| T-12 | Pago parcial y reintento | No excede obligación; sin doble registro |
| T-13 | Presupuesto 100 y gasto 30 | Uso 30%; disponible 70 |
| T-14 | Dashboard sin movimientos | Ceros/estados vacíos, sin errores |
| T-15 | Cambio de hogar activo | No hereda selección ni cache de otro hogar |
| T-16 | UI 360px + navegación teclado | Sin scroll horizontal y acciones operables |
| T-17 | Consulta 10k movimientos paginados | sin respuesta ilimitada ni N+1 críticos |
| T-18 | Restauración de backup de ensayo | Datos íntegros tras restore |

## Definición de terminado (DoD)

### Cobertura Fase 1 financiera

`backend/tests/test_finance.py` verifica apertura/saldos, gastos/ingresos/transferencias,
corrección/anulación/auditoría, precisión/fechas, roles/CSRF, aislamiento, filtros,
dashboard, rollback y escrituras concurrentes idénticas sobre PostgreSQL real.
También prueba rechazo de ledger parcial/mutable y FKs cruzadas desde ORM.
Las pruebas Angular de finance verifican formularios, errores, confirmación móvil,
reintentos/doble envío, refresco y aislamiento de respuestas al cambiar hogar.
T-01/02/05/06/07/08/14/15 cubiertos; T-16/17 requieren navegador y medición real.
Resultados y limitaciones en [estado](../10_planificacion/estado_implementacion.md).

Requisito trazado; migración reversible o estrategia documentada; tests de casos felices y negativos; permiso tenant probado; observabilidad sin PII; API documentada; interfaz responsive/accesible; revisión de código; despliegue repetible. Ninguna fase se marca completa con solo endpoints o mockups.
