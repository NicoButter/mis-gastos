# 01 · Visión y alcance

## Problema

Las familias manejan gastos dispersos entre efectivo, bancos, billeteras y tarjetas. La carga diaria suele ser tediosa; los reportes confunden transferencias, consumos y pagos de resúmenes, provocando doble contabilización.

## Propuesta

Gastio ofrece un registro rápido (móvil), una rutina opcional de revisión diaria y un centro de control familiar (desktop) con presupuesto, tarjetas, cuotas y compromisos futuros.

## Personas

- **Titular del hogar**: configura integrantes, cuentas, categorías y permisos.
- **Miembro adulto**: registra y consulta movimientos conforme permisos.
- **Miembro de carga limitada**: registra gastos en cuentas habilitadas, sin acceder necesariamente a totales.
- **Operador de plataforma**: administra salud operativa, planes y soporte sin acceso ordinario a datos financieros de hogares.

## Principios

1. Una carga ordinaria requiere monto, categoría y cuenta; el resto se infiere de valores predeterminados editables.
2. El hogar es tenant. Una cuenta de usuario puede pertenecer a varios hogares; elige hogar activo.
3. Los datos de hogares distintos no se mezclan nunca, ni en consultas, exportaciones o tareas asíncronas.
4. Una compra con tarjeta y el pago de su resumen no se cuentan dos veces como consumo.
5. No se prometen saldos bancarios reales ni asesoramiento financiero.
6. Se priorizan accesibilidad, privacidad y simplicidad.

## Alcance MVP

- Registro/inicio de sesión, creación de hogar, invitaciones, roles y selección del hogar activo.
- Cuentas manuales (efectivo/banco/billetera), categorías, ingreso, gasto, transferencia.
- Consulta, búsqueda, filtros, corrección y anulación de movimientos con auditoría.
- Tarjetas de crédito manuales, compras en cuotas y calendario de obligaciones previsto.
- Presupuestos mensuales por categoría, tablero y reporte del mes.
- Flujo móvil de carga rápida, adaptable e instalable como PWA online.
- Moneda base ARS; estructura preparada para otras monedas sin consolidación FX automática.

## Posterior al MVP

- **V1:** gastos recurrentes con instancias confirmables, objetivos de ahorro, cierre diario, exportaciones CSV/PDF, notificaciones y más análisis.
- **Futuro:** sincronización offline, OCR de comprobantes, carga por lenguaje natural, múltiples monedas con tipos de cambio, integraciones bancarias, suscripciones pagas, app nativa.

## Fuera de alcance

Banca transaccional, pagos reales, inversiones, declaración impositiva, conciliación automática bancaria, presupuestos predictivos con garantías y crédito.

## Métricas de producto

- Porcentaje de hogares activos semanalmente; tiempo mediano para crear un gasto; tasa de registros corregidos; finalización de onboarding; discrepancias reportadas en cálculos de tarjetas.

## Supuestos y decisiones abiertas

- Marca provisional: **Gastio**; validar disponibilidad marcaria y de dominio antes de la salida pública.
- Privacidad entre miembros: en MVP, visibilidad por cuenta habilitada; política de movimientos privados avanzados pendiente de ADR.
- Planes de suscripción: previstos en arquitectura pero no facturados en MVP.
