# Gastio — Revisión previa a publicar textos legales

**Este archivo es interno; NO debe mostrarse como página pública.**

## Identidad y atención al usuario

- [ ] Confirmar nombre o razón social legal que opera Gastio (Vetrabyte es marca, no necesariamente sujeto legal).
- [ ] CUIT, domicilio y correo válido de contacto/privacidad/seguridad.
- [ ] Dominio final del servicio y rutas públicas.
- [ ] Revisar términos y política con profesional legal argentino.
- [ ] Definir reglas para menores y la funcionalidad de registro correspondiente.

## Datos y seguridad

- [ ] Identificar hosting de producción y países de almacenamiento y copias; evaluar transferencia internacional y garantías.
- [ ] Documentar subencargados (hosting, correo, Google, monitoreo) y sus funciones reales.
- [ ] Verificar HTTPS, cookies Secure/HttpOnly/SameSite, CSRF, permisos por hogar, backups y acceso operacional.
- [ ] Definir retención, eliminación y copia de seguridad (plazos comprobables), incluyendo historiales compartidos.
- [ ] Confirmar si existe analytics, email transaccional o cookies adicionales; actualizar textos si corresponde.
- [ ] Verificar canal de ejercicio de derechos y procedimiento de verificación de identidad; derechos de ley 25.326.
- [ ] Determinar procedimiento de reporte y manejo de incidentes.
- [ ] Verificar posibilidad real de exportación, eliminación y baja; no prometer controles que todavía no existen.

## Consentimiento y presentación

- [ ] Publicar `/terminos`, `/privacidad`, `/como-funciona`, `/seguridad` accesibles sin login y desde el footer.
- [ ] Vincular política de privacidad pública en Google Auth Platform / pantalla OAuth.
- [ ] Registrar aceptación de términos y versión aplicable en onboarding, sin casilla premarcada; distinguir información de privacidad del consentimiento cuando corresponda.
- [ ] Permitir lectura de textos legales desde login y landing; evitar bloquear su acceso con guards de Angular.
- [ ] Mantener versión, fecha de entrada en vigencia e historial de cambios.
- [ ] Garantizar accesibilidad móvil y enlaces claros.

## Si se habilitan suscripciones comerciales a Gastio

- [ ] Informar precio total, impuestos, frecuencia, renovaciones y condiciones antes del cobro.
- [ ] Implementar mecanismos de baja, confirmación y, cuando aplique, botón de arrepentimiento según normativa argentina vigente.
- [ ] Revisar ley 24.240, Disposición 954/2025 y Disposición 3/2026 según el modelo comercial efectivo.
- [ ] No confundir los pagos recurrentes que el usuario registra con las suscripciones comerciales de Gastio.

## Fuentes de referencia oficial (consultadas en octubre de 2026)

- Ley 25.326 de Protección de Datos Personales: https://www.argentina.gob.ar/normativa/nacional/64790/actualizacion
- Derechos de titulares, AAIP: https://www.argentina.gob.ar/aaip/datospersonales/derechos
- Obligaciones de responsables, AAIP: https://www.argentina.gob.ar/aaip/datospersonales/responsables/obligaciones
- Transferencias internacionales, AAIP: https://www.argentina.gob.ar/transferencias-internacionales
- Ley 24.240, defensa del consumidor: https://www.argentina.gob.ar/normativa/nacional/638/actualizacion
- Disposición 954/2025: https://www.argentina.gob.ar/normativa/nacional/norma-417152/texto
- Disposición 3/2026: https://www.argentina.gob.ar/normativa/nacional/disposici%C3%B3n-3-2026-423007/texto
- Política Google OAuth: https://developers.google.com/identity/protocols/oauth2/policies
- Página web y política de privacidad en verificación de marca Google: https://developers.google.com/identity/protocols/oauth2/production-readiness/brand-verification
