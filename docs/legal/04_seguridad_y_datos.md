# Cómo cuidamos tus datos en Mis Gastos

**Versión:** 0.1 · Resumen de seguridad para usuarios · Octubre de 2026

## Sabemos que tus finanzas son privadas

Cuando registrás cuánto cobrás, qué comprás o qué pagos tenés pendientes, estás confiando información importante. Por eso, Mis Gastos se diseñó para limitar el acceso a esos registros y mantener un historial consistente de las operaciones.

## Autenticación con Google

Utilizamos Google OpenID Connect para identificarte, y Mis Gastos administra su propia sesión. No te pedimos una contraseña adicional para Mis Gastos ni solicitamos permisos para leer tu Gmail, tus contactos o tus cuentas bancarias.

## Hogares separados

Los datos se organizan por hogar. La API verifica que el usuario pertenezca al hogar antes de permitir acceso a sus recursos. Los roles y permisos ayudan a definir qué puede hacer cada integrante autorizado. **Esto no significa que los datos sean secretos frente a otras personas autorizadas del mismo hogar.**

## Protección de operaciones

La implementación reportada incluye controles CSRF para acciones autenticadas, verificaciones de permisos, transacciones de base de datos, idempotencia para evitar duplicados accidentales y un historial trazable de correcciones y anulaciones.

Estos controles reducen riesgos, pero no sustituyen una revisión periódica de seguridad ni garantizan que no pueda ocurrir un incidente.

## Tarjetas sin datos innecesarios

Mis Gastos permite organizar compras con tarjeta, pero no necesita almacenar el número completo, el CVV o el PIN. No ingreses datos bancarios secretos en descripciones ni notas.

## Comunicación y alojamiento

La configuración de producción debe ofrecer HTTPS y cookies de sesión seguras. **Antes de publicar esta página se verificará la configuración real desplegada**, junto con el proveedor de alojamiento, el país donde se almacenan los datos y las políticas de respaldo y recuperación.

No declaramos cifrado de la base de datos en reposo, auditorías externas, certificaciones o tiempos específicos de recuperación que todavía no hayan sido comprobados.

## Acceso del personal y proveedores

El acceso de soporte o administración a datos personales debe limitarse a casos justificados y personal autorizado, aplicando medidas técnicas y organizativas apropiadas. Los proveedores que participen en el servicio deben identificarse en la Política de privacidad y cumplir las obligaciones aplicables.

## Vos también podés ayudar

- Protegé tu cuenta Google y activá la verificación en dos pasos si está disponible.
- Cerrá sesión en dispositivos compartidos.
- Revisá los integrantes y permisos de cada hogar.
- No cargues contraseñas, números completos de tarjetas ni códigos de seguridad en campos de texto.
- Contrastá saldos y vencimientos con tus fuentes originales.
- Informá accesos sospechosos a [CORREO DE SEGURIDAD].

## Control de tu información

Podés solicitar acceso, actualización, rectificación y, cuando corresponda, eliminación de tus datos personales. Revisá las condiciones y el contacto en nuestra [Política de privacidad](./02_politica_de_privacidad.md).

---

**Importante:** este texto comunica medidas identificadas en la arquitectura reportada. Se requiere revisar la configuración real y los procesos operativos antes de utilizarlo como declaración definitiva de seguridad.
