# Gastio — Política de privacidad

**Versión:** 0.1 (borrador para revisión)  
**Fecha de preparación:** 13 de octubre de 2026  
**Entrada en vigencia:** [COMPLETAR ANTES DE PUBLICAR]  
**Responsable del tratamiento:** [NOMBRE O RAZÓN SOCIAL LEGAL — NO SOLO LA MARCA VETRABYTE]  
**CUIT / domicilio:** [COMPLETAR]  
**Contacto para ejercer derechos:** [CORREO DE PRIVACIDAD]  
**Sitio web:** [DOMINIO DE PRODUCCIÓN]

> Este documento describe el funcionamiento conocido de Gastio. Los datos sobre proveedores de alojamiento, países de almacenamiento, copias de seguridad, plazos de retención y canales de derechos **deben verificarse e incorporarse antes de su publicación**.

## 1. Nuestro compromiso

En Gastio entendemos que los registros de ingresos, gastos, deudas y presupuestos son información privada. Tratamos los datos para ofrecer el servicio, mantener su seguridad, solucionar errores y cumplir las obligaciones aplicables. **No usamos tus registros financieros para vender perfiles comerciales ni los publicamos como datos abiertos.** Esta declaración debe mantenerse coherente con las operaciones reales del servicio.

## 2. Qué datos podemos tratar

**Perfil e identificación:** nombre, dirección de correo electrónico, identificador de cuenta y, si se utiliza, imagen de perfil proporcionada por Google o elegida por vos.

**Autenticación:** identificador técnico de la cuenta Google, estado de sesión y datos indispensables para verificar el acceso. Solicitamos los permisos `openid`, `email` y `profile` para iniciar sesión; **no solicitamos acceso al contenido de Gmail, Google Drive, contactos ni cuentas bancarias**.

**Información financiera ingresada:** nombres y tipos de cuentas, saldos iniciales, ingresos, gastos, categorías, descripciones, transferencias, tarjetas identificadas sin número completo, compras, cuotas, resúmenes, pagos, recurrencias y fechas de vencimiento. Estos datos los ingresan o confirman las personas usuarias.

**Hogares compartidos:** hogar al que pertenecés, rol, membresías y acciones autorizadas. Los movimientos y compromisos compartidos pueden ser visibles para otros integrantes autorizados del mismo hogar.

**Información técnica y de seguridad:** dirección IP, datos técnicos de conexión y navegador, cookies necesarias, fechas de acceso, errores, intentos de autenticación y registros de actividad, según lo que efectivamente recojan y conserven los sistemas de producción.

Gastio no requiere que cargues números completos de tarjetas, códigos CVV, claves de home banking ni contraseñas de entidades financieras. **No ingreses estos datos en campos libres o descripciones**.

## 3. Para qué usamos los datos

- Autenticar usuarios mediante Google y gestionar sesiones.
- Administrar hogares, membresías y permisos.
- Guardar movimientos y calcular saldos, resúmenes, vencimientos y compromisos.
- Permitir revisiones, correcciones, anulaciones y trazabilidad de operaciones.
- Proteger el servicio frente a errores y accesos no autorizados.
- Atender consultas y solicitudes de derechos.
- Cumplir obligaciones legales aplicables.

No se usarán datos para publicidad personalizada, cesión comercial ni analítica de terceros sin informar previamente el nuevo tratamiento y cumplir las condiciones legales pertinentes.

## 4. Fundamento del tratamiento

La creación de una cuenta y la prestación de las funciones solicitadas requieren tratar los datos necesarios para ejecutar el servicio. Cuando la normativa argentina exija consentimiento, se solicitará de forma informada; determinados tratamientos podrán estar respaldados en las excepciones legalmente previstas y en obligaciones aplicables. Los tratamientos opcionales se comunicarán por separado si se incorporan.

## 5. Quiénes pueden acceder

- **Vos**, desde tu cuenta autenticada.
- **Integrantes autorizados de tu hogar**, de acuerdo con los roles y funciones compartidas habilitadas. Un hogar no da acceso a otro hogar.
- **Personal autorizado para operación o soporte**, únicamente en la medida necesaria, sujeto a obligaciones de confidencialidad y controles adecuados. [DESCRIBIR PROCESO REAL DE SOPORTE/ACCESO].
- **Proveedores de servicios tecnológicos necesarios**, tales como autenticación o alojamiento, sujetos a sus funciones y condiciones aplicables. [IDENTIFICAR PROVEEDORES, FINALIDADES Y UBICACIONES].
- **Autoridades**, cuando exista un requerimiento legal válido.

No vendemos ni publicamos el historial financiero de los hogares.

## 6. Acceso con Google

Al elegir «Continuar con Google», Google gestiona la autenticación y comparte los datos de identidad autorizados por vos para permitir el ingreso a Gastio. Gastio conserva una cuenta y sesión propias. Podés revisar o revocar el acceso concedido desde la configuración de tu cuenta Google; revocarlo puede impedir futuros ingresos hasta reautorizar el servicio, pero **no implica por sí mismo la eliminación automática de tu historial de Gastio**.

Para conocer cómo trata Google los datos en sus propios servicios, consultá su política de privacidad: https://policies.google.com/privacy

## 7. Cookies y tecnologías equivalentes

Gastio utiliza cookies y mecanismos técnicos necesarios para **mantener la sesión, prevenir solicitudes no autorizadas y permitir la navegación autenticada**. Su existencia, nombre y duración exactos deben confirmarse en producción.

| Categoría | Uso previsto | Situación |
|---|---|---|
| Sesión / autenticación | Mantener la sesión Django | Necesaria |
| CSRF / seguridad | Proteger acciones autenticadas | Necesaria |
| Preferencias de interfaz | Recordar ajustes locales si se implementan | [VERIFICAR] |
| Analítica / publicidad | No declarada en la versión actual | No incorporar sin actualizar esta política |

Las cookies técnicas necesarias no sirven por sí mismas para vender datos de consumo. Si en el futuro se incorporan cookies no esenciales, se informarán sus finalidades y se gestionará el consentimiento correspondiente cuando sea exigible.

## 8. Seguridad

La arquitectura comunicada del proyecto incluye autenticación con Google, sesiones Django, protección CSRF, validación de permisos por hogar, comprobaciones de integridad y auditoría de operaciones. En producción debe verificarse el uso de HTTPS y la configuración efectiva de cookies y controles de acceso.

**No afirmamos que todos los datos estén cifrados en reposo, que existan auditorías externas o que los respaldos tengan un plazo concreto** sin comprobar esas medidas. Ninguna plataforma puede garantizar riesgo cero.

Más información: [Seguridad y protección de datos](./04_seguridad_y_datos.md).

## 9. Almacenamiento y transferencias internacionales

Los datos pueden ser procesados por infraestructura de alojamiento y proveedores tecnológicos cuya identificación y localización deberá informarse aquí antes de publicar: **[PROVEEDOR DE HOSTING, PAÍS DE ALOJAMIENTO, PAÍS DE RESPALDOS, OTROS ENCARGADOS]**.

Si existe transferencia internacional de datos, se evaluará su adecuación y las garantías exigidas por la normativa argentina. **No debe publicarse una afirmación genérica de que todos los datos permanecen en Argentina si el servidor o los respaldos se alojan en el exterior.**

## 10. Conservación de datos

Conservamos los datos durante el período necesario para prestar el servicio y atender obligaciones, reclamos y necesidades justificadas de integridad y seguridad. Antes del lanzamiento deben determinarse las reglas efectivas y verificables para:

- Datos de perfil y cuenta: [PLAZO / CRITERIO].
- Movimientos y registros de hogares: [PLAZO / CRITERIO Y SUPUESTOS DE BAJA].
- Registros de auditoría y seguridad: [PLAZO / CRITERIO].
- Respaldos y eliminación diferida: [PLAZO Y PROCEDIMIENTO].

Los registros de un hogar compartido pueden requerir conservación incluso si una persona deja de participar, sin perjuicio de los derechos de rectificación o supresión que correspondan legalmente.

## 11. Tus derechos

De acuerdo con la Ley argentina 25.326, podés solicitar **acceso, rectificación, actualización y, cuando corresponda, supresión** de tus datos personales, así como otros derechos que reconozca la normativa aplicable.

Escribí a **[CORREO DE PRIVACIDAD]** indicando la solicitud. Podemos pedir una verificación de identidad proporcionada. No solicitaremos contraseñas ni códigos de acceso para ejercer derechos.

Como referencia, la normativa prevé respuesta a pedidos de acceso dentro de **10 días corridos** y tratamiento de solicitudes de rectificación o supresión dentro de **5 días hábiles**, sujetos a los supuestos y condiciones legales. La supresión puede tener excepciones, como obligaciones de conservación o derechos de terceros.

También podés acudir a la **Agencia de Acceso a la Información Pública (AAIP)**: https://www.argentina.gob.ar/aaip/datospersonales/derechos

## 12. Menores de edad

[DEFINIR Y PUBLICAR LA POLÍTICA DE EDAD Y, SI APLICA, EL PROCEDIMIENTO PARA TUTORES. NO AFIRMAR QUE LA PLATAFORMA COMPRUEBA LA EDAD SI NO LO HACE].

## 13. Incidentes de seguridad

Si identificamos un incidente que pueda afectar datos personales, investigaremos, adoptaremos medidas razonables de contención y realizaremos las comunicaciones que correspondan conforme a la ley y al riesgo observado. Para reportar una posible vulnerabilidad o acceso indebido: [CORREO DE SEGURIDAD].

## 14. Actualizaciones de esta política

Publicaremos una fecha de vigencia y comunicaremos los cambios significativos. Si incorporamos nuevas finalidades o terceros que requieran una autorización adicional, gestionaremos el consentimiento correspondiente antes de iniciar el tratamiento.

---

**Más información:** [Términos y condiciones](./01_terminos_y_condiciones.md) · [Cómo funciona](./03_como_funciona.md) · [Seguridad](./04_seguridad_y_datos.md)
