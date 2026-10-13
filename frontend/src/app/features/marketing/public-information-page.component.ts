import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

interface InformationSection {
  heading: string;
  paragraphs: string[];
  bullets?: string[];
}

interface PublicDocument {
  title: string;
  version: string;
  preparedDate: string;
  effectiveDate: string;
  sections: InformationSection[];
}

const documents: Record<string, PublicDocument> = {
  terms: {
    title: "Términos y condiciones de uso",
    version: '0.1',
    preparedDate: '13 de octubre de 2026',
    effectiveDate: '13 de octubre de 2026',
    sections: [
      {
        heading: "1. Qué es Gastio",
        paragraphs: [
          "Gastio es una aplicación para organizar y consultar las finanzas personales y familiares. Permite registrar cuentas, saldos iniciales, ingresos, gastos, transferencias, compras con tarjeta, cuotas, compromisos mensuales y pagos recurrentes.",
          "Los resúmenes se elaboran a partir de los datos cargados. Gastio no realiza pagos ni transferencias de dinero y no presta asesoramiento financiero, contable, impositivo o jurídico. Marcar una cuota como pagada no realiza el pago fuera de la aplicación.",
        ],
      },
      {
        heading: "2. Uso del servicio",
        paragraphs: [
          "El uso de Gastio se rige por estos términos. La Política de privacidad explica cómo se trata la información personal. Las funciones disponibles pueden evolucionar mediante actualizaciones del servicio.",
        ],
      },
      {
        heading: "3. Cuenta y acceso con Google",
        paragraphs: [
          "El acceso se realiza con Google. Gastio utiliza los datos de identidad autorizados para crear o recuperar la cuenta y administrar la sesión.",
          "Cada usuario debe proteger su cuenta de Google, proporcionar información veraz y cerrar sesión en dispositivos compartidos.",
        ],
      },
      {
        heading: "4. Hogares compartidos y permisos",
        paragraphs: [
          "Los datos financieros se organizan por hogar. Sus integrantes autorizados pueden consultar la información compartida según los permisos asignados. No cargues información que no quieras compartir con los demás integrantes autorizados.",
          "La administración de cada hogar debe revisar sus integrantes y permisos. Pertenecer a un hogar no permite acceder a los datos de otros hogares. Los registros aportados pueden permanecer en el historial compartido para conservar la coherencia de las cuentas, sin perjuicio de los derechos sobre los datos personales.",
        ],
      },
      {
        heading: "5. Datos financieros y exactitud",
        paragraphs: [
          "Los importes, categorías, fechas, saldos y vencimientos dependen de la información ingresada o confirmada por los usuarios. Revisá los registros frente a comprobantes, extractos y acuerdos reales.",
          "Un saldo inicial no es un ingreso nuevo. Las transferencias entre cuentas modifican saldos sin generar por sí mismas ingresos o gastos. Las cuotas y recurrencias representan compromisos y no producen débitos automáticos.",
          "Los pagos deben distinguirse de las compras de origen para evitar duplicaciones. Las correcciones y anulaciones se realizan según las funciones y permisos disponibles, conservando la trazabilidad de las operaciones.",
        ],
      },
      {
        heading: "6. Uso permitido",
        paragraphs: [
          "El servicio está destinado a actividades lícitas. No se permite acceder a hogares ajenos, eludir permisos, introducir código malicioso, abusar de la API ni generar tráfico que perjudique la plataforma.",
          "Gastio podrá limitar el acceso ante abusos comprobados o cuando sea necesario para proteger la integridad del servicio, respetando los derechos aplicables.",
        ],
      },
      {
        heading: "7. Disponibilidad y mantenimiento",
        paragraphs: [
          "El servicio puede requerir mantenimiento, actualizaciones o interrupciones. Se procurará informar los cambios relevantes y corregir las incidencias conocidas. Ningún sistema puede garantizar disponibilidad continua o seguridad absoluta.",
          "Conservá los comprobantes y documentación originales de tus operaciones. Los registros de Gastio no sustituyen la documentación de bancos, emisores de tarjetas o acreedores.",
        ],
      },
      {
        heading: "8. Precios y suscripciones",
        paragraphs: [
          "Esta versión no define planes pagos ni cargos recurrentes de Gastio. Si se incorporan, se informarán previamente el precio, la frecuencia, la forma de pago, la renovación y las condiciones de cancelación, y se solicitará la aceptación correspondiente.",
          "Los gastos recurrentes registrados por un usuario son sus propios compromisos financieros y no constituyen una suscripción a Gastio.",
        ],
      },
      {
        heading: "9. Privacidad",
        paragraphs: [
          "El tratamiento de los datos de identificación, registros financieros, membresías, sesiones y actividad técnica se describe en la Política de privacidad, disponible desde esta página y desde el acceso al servicio.",
        ],
      },
      {
        heading: "10. Cierre de cuenta y datos compartidos",
        paragraphs: [
          "La baja y las solicitudes de eliminación están sujetas a verificación de identidad y a los derechos aplicables. La baja no implica necesariamente la eliminación inmediata de registros compartidos, datos de auditoría o información sujeta a obligaciones de conservación.",
          "Revocar el acceso desde Google no elimina automáticamente el historial registrado en Gastio.",
        ],
      },
      {
        heading: "11. Propiedad intelectual",
        paragraphs: [
          "El diseño, las marcas, los textos, el código y los elementos originales de Gastio pertenecen a sus respectivos titulares. Su uso se rige por las licencias y condiciones aplicables. Los usuarios conservan los derechos que les correspondan sobre los datos que cargan.",
        ],
      },
      {
        heading: "12. Responsabilidad",
        paragraphs: [
          "Los usuarios deben verificar sus datos antes de tomar decisiones económicas. Los resúmenes dependen de la exactitud y actualización de los registros ingresados.",
          "Estos términos no excluyen derechos irrenunciables de los consumidores ni responsabilidades que no puedan limitarse conforme a la normativa aplicable.",
        ],
      },
      {
        heading: "13. Actualizaciones",
        paragraphs: [
          "Los términos podrán actualizarse por cambios funcionales, normativos o de seguridad. La versión y fecha se muestran al inicio del documento. Los cambios sustanciales se comunicarán y se solicitará nueva aceptación cuando corresponda.",
        ],
      },
      {
        heading: "14. Ley aplicable",
        paragraphs: [
          "Estos términos se interpretan conforme a las normas aplicables en la República Argentina, respetando los derechos de los consumidores y la competencia de las autoridades correspondientes.",
        ],
      },
    ],
  },
  privacy: {
    title: "Política de privacidad",
    version: '0.1',
    preparedDate: '13 de octubre de 2026',
    effectiveDate: '13 de octubre de 2026',
    sections: [
      {
        heading: "1. Privacidad en Gastio",
        paragraphs: [
          "Gastio trata información personal para prestar el servicio, mantener su seguridad, resolver errores y cumplir las obligaciones aplicables. Los registros financieros de los hogares no se venden ni se publican como datos abiertos.",
        ],
      },
      {
        heading: "2. Datos que se tratan",
        paragraphs: [
          "La información de perfil incluye nombre, correo electrónico, identificador de cuenta y, cuando se utiliza, imagen de perfil. La autenticación utiliza datos de identidad proporcionados por Google y los datos necesarios para mantener la sesión.",
          "Los registros financieros incluyen cuentas, saldos, ingresos, gastos, categorías, descripciones, transferencias, tarjetas sin número completo, compras, cuotas, pagos, recurrencias y vencimientos ingresados por los usuarios.",
          "También se tratan las membresías y permisos de los hogares, los registros de actividad y los datos técnicos de conexión necesarios para operar y proteger el servicio. No ingreses números completos de tarjetas, CVV, PIN ni claves bancarias en campos libres.",
        ],
      },
      {
        heading: "3. Finalidades",
        paragraphs: [
          "Los datos permiten autenticar usuarios, administrar hogares y permisos, guardar movimientos, calcular saldos y vencimientos, conservar la trazabilidad de las operaciones y prevenir accesos no autorizados.",
          "No se utilizan los registros financieros para publicidad personalizada ni para vender perfiles comerciales. Los tratamientos opcionales o nuevas finalidades se informarán por separado.",
        ],
      },
      {
        heading: "4. Fundamento del tratamiento",
        paragraphs: [
          "Se trata la información necesaria para brindar las funciones solicitadas y cumplir las obligaciones aplicables. Cuando un tratamiento requiera consentimiento, se solicitará de forma informada.",
        ],
      },
      {
        heading: "5. Acceso a la información",
        paragraphs: [
          "Cada usuario accede a su información mediante una sesión autenticada. Los integrantes de un hogar pueden acceder a sus registros compartidos según los permisos asignados.",
          "El acceso operativo o de soporte se limita a personal autorizado y a lo necesario para prestar y proteger el servicio. Los proveedores tecnológicos intervienen según sus funciones. La información también podrá entregarse a autoridades ante un requerimiento legal válido.",
        ],
      },
      {
        heading: "6. Autenticación con Google",
        paragraphs: [
          "Google gestiona la autenticación y comparte los datos de identidad autorizados para ingresar a Gastio. Se utilizan los permisos de identidad, correo y perfil; iniciar sesión no otorga acceso a Gmail, Google Drive, contactos ni cuentas bancarias.",
          "Podés revisar o revocar el acceso desde tu cuenta de Google. Revocarlo puede impedir futuros ingresos, pero no elimina automáticamente los registros de Gastio. El tratamiento que realiza Google en sus servicios se describe en su propia política de privacidad.",
        ],
      },
      {
        heading: "7. Cookies y preferencias",
        paragraphs: [
          "Gastio utiliza cookies de sesión y de protección CSRF para mantener el acceso y proteger las acciones autenticadas. Las preferencias de interfaz pueden guardarse localmente en el navegador.",
          "Si se incorporan tecnologías no esenciales, se informarán sus finalidades y se solicitará el consentimiento que corresponda.",
        ],
      },
      {
        heading: "8. Seguridad",
        paragraphs: [
          "Gastio utiliza autenticación, controles de acceso por hogar, validaciones de integridad y un historial de operaciones para proteger los registros. Evitá guardar secretos bancarios y protegé la cuenta de Google utilizada para ingresar.",
          "Las medidas de seguridad reducen riesgos, pero ningún sistema puede garantizar que no ocurran incidentes. Consultá también la página de Seguridad y protección de datos.",
        ],
      },
      {
        heading: "9. Almacenamiento y proveedores",
        paragraphs: [
          "El servicio utiliza infraestructura tecnológica para almacenar y procesar los registros. Google interviene en la autenticación. El tratamiento por proveedores y las transferencias internacionales están sujetos a las condiciones y garantías exigidas por la normativa aplicable.",
        ],
      },
      {
        heading: "10. Conservación",
        paragraphs: [
          "Los datos se conservan durante el tiempo necesario para prestar el servicio y atender obligaciones aplicables, reclamos y necesidades justificadas de integridad y seguridad.",
          "Los registros de un hogar compartido pueden requerir conservación cuando una persona deja de participar. La eliminación puede estar sujeta a obligaciones de conservación, derechos de terceros y ciclos de respaldo.",
        ],
      },
      {
        heading: "11. Derechos sobre los datos",
        paragraphs: [
          "Podés solicitar acceso, actualización, rectificación y, cuando corresponda, eliminación de tus datos personales conforme a la normativa aplicable. La solicitud puede requerir una verificación de identidad proporcionada; no se deben compartir contraseñas ni códigos de acceso.",
          "También podés acudir a la Agencia de Acceso a la Información Pública (AAIP), autoridad argentina en materia de protección de datos personales.",
        ],
      },
      {
        heading: "12. Información de otras personas",
        paragraphs: [
          "Cargá únicamente información que estés autorizado a registrar y compartir. Evitá incluir datos personales innecesarios de otras personas, especialmente de menores, en notas o descripciones.",
        ],
      },
      {
        heading: "13. Incidentes de seguridad",
        paragraphs: [
          "Ante un incidente que afecte datos personales, se investigará su alcance y se adoptarán medidas de contención y las comunicaciones que correspondan conforme a la normativa y al riesgo observado.",
        ],
      },
      {
        heading: "14. Actualizaciones de esta política",
        paragraphs: [
          "La versión y la fecha de esta política se muestran al inicio. Los cambios significativos se comunicarán y, si se incorporan tratamientos que requieran autorización adicional, se solicitará antes de iniciarlos.",
        ],
      },
    ],
  },
  howItWorks: {
    title: 'Cómo funciona Gastio',
    version: '0.1 · guía pública',
    preparedDate: 'Octubre de 2026',
    effectiveDate: 'No aplica; guía informativa',
    sections: [
      {
        heading: 'Tus gastos, tus cuentas, todo más claro',
        paragraphs: [
          'Gastio te ayuda a llevar un registro de cuánto dinero entra, cuánto gastás, cuánto tenés disponible y qué pagos se acercan. Está pensado para personas y familias que quieren organizarse sin conocimientos contables ni planillas complicadas.',
        ],
      },
      {
        heading: '1. Entrá con Google',
        paragraphs: [
          'Elegí «Continuar con Google». Gastio usa esa cuenta para reconocerte sin pedirte una contraseña nueva. No accede a tus correos de Gmail ni a tus cuentas bancarias por iniciar sesión.',
        ],
      },
      {
        heading: '2. Creá tu hogar',
        paragraphs: [
          'Un hogar es el espacio donde se organizan los movimientos financieros. Podés tener un hogar personal o compartirlo con familiares autorizados. Cada hogar mantiene sus propios datos, cuentas y registros.',
          'Los movimientos ingresados en un hogar compartido pueden ser visibles para sus miembros autorizados, según sus roles.',
        ],
      },
      {
        heading: '3. Agregá tus cuentas',
        paragraphs: [
          'Registrá dónde administrás tu dinero: efectivo, banco o billetera virtual. Podés indicar el saldo inicial. Ese importe representa el dinero que ya tenías y no se considera un nuevo ingreso del mes.',
        ],
      },
      {
        heading: '4. Registrá ingresos y gastos',
        paragraphs: [
          'Cuando cobrás un sueldo o recibís un ingreso, registrá su importe, fecha, categoría y cuenta. Cuando gastás, elegí la cuenta de origen y la categoría. El saldo y los resúmenes se actualizan a partir de tus registros.',
          'Podés utilizar la carga rápida desde el celular para registrar un gasto con pocos pasos.',
        ],
      },
      {
        heading: '5. Transferí entre cuentas',
        paragraphs: [
          'Si pasás dinero de un banco a una billetera virtual, registrá una transferencia. Gastio disminuye una cuenta y aumenta la otra, sin contarlo como un gasto o ingreso nuevo.',
        ],
      },
      {
        heading: '6. Controlá tarjetas y cuotas',
        paragraphs: [
          'Podés registrar tarjetas y compras en uno o varios pagos, consultar cuotas pendientes y registrar los pagos. No necesitás ingresar el número completo de la tarjeta ni su código de seguridad.',
          'También podés registrar una compra en cuotas sin tarjeta. Las cuotas representan compromisos; al pagar, elegís de qué cuenta sale el dinero.',
        ],
      },
      {
        heading: '7. Agendá gastos recurrentes',
        paragraphs: [
          'Podés configurar compromisos mensuales, consultar próximos vencimientos, confirmar pagos, ajustar importes o pausar la recurrencia.',
          'Registrar una recurrencia no significa que Gastio cobre automáticamente el servicio ni que pague por vos.',
        ],
      },
      {
        heading: '8. Mirá el dashboard',
        paragraphs: [
          'El resumen principal permite consultar ingresos y gastos registrados durante el período, saldo disponible en las cuentas líquidas y próximos compromisos pendientes.',
          'El saldo disponible no es necesariamente igual a «ingresos menos gastos del mes»: también depende de saldos iniciales, movimientos de otros períodos y pagos efectivos.',
        ],
        bullets: [
          'Ingresos del mes: lo que cobraste y registraste durante el período.',
          'Gastos del mes: consumos registrados, evitando contar dos veces pagos relacionados.',
          'Saldo disponible: dinero registrado en tus cuentas líquidas.',
          'Próximos compromisos: tarjetas, cuotas y servicios que todavía tenés que pagar.',
        ],
      },
      {
        heading: '¿Gastio mueve dinero o se conecta a mi banco?',
        paragraphs: [
          'No. Gastio es una herramienta de registro manual. No inicia transferencias, no debita automáticamente tu cuenta y no verifica importes contra tu banco. Vos confirmás los pagos y movimientos que querés registrar.',
        ],
      },
      {
        heading: '¿Mis datos son públicos?',
        paragraphs: [
          'La aplicación está diseñada para permitir el acceso de usuarios autenticados, limitando los datos a sus hogares autorizados. Los datos de un hogar compartido pueden estar disponibles para otros integrantes según sus permisos.',
        ],
      },
      {
        heading: '¿Puedo equivocarme al registrar algo?',
        paragraphs: [
          'Podés corregir o anular movimientos conforme a las funciones y permisos disponibles. Siempre conviene comparar los datos con comprobantes reales.',
        ],
      },
      {
        heading: '¿Necesito conocimientos de finanzas?',
        paragraphs: [
          'No. La idea es simple: cargar lo que entra, lo que sale y lo que falta pagar, y consultar el resumen cuando lo necesitás.',
        ],
      },
    ],
  },
  security: {
    title: 'Seguridad y protección de datos',
    version: '0.1 · resumen para usuarios',
    preparedDate: 'Octubre de 2026',
    effectiveDate: 'No aplica; resumen informativo',
    sections: [
      {
        heading: 'Sabemos que tus finanzas son privadas',
        paragraphs: [
          'Gastio se diseñó para limitar el acceso a los registros financieros y mantener un historial consistente de las operaciones.',
        ],
      },
      {
        heading: 'Acceso con Google',
        paragraphs: [
          'Gastio utiliza Google OpenID Connect para identificarte y administra su propia sesión. No te pide una contraseña adicional ni solicita permisos para leer Gmail, contactos o cuentas bancarias.',
        ],
      },
      {
        heading: 'Separación de hogares',
        paragraphs: [
          'Los datos se organizan por hogar. El acceso depende de la pertenencia y los permisos asignados. Esto no significa que los datos sean secretos frente a otras personas autorizadas del mismo hogar.',
        ],
      },
      {
        heading: 'Protección de operaciones',
        paragraphs: [
          'Gastio incluye controles CSRF para acciones autenticadas, verificaciones de permisos, transacciones de base de datos, idempotencia para evitar duplicados accidentales y un historial trazable de correcciones y anulaciones.',
          'Estos controles reducen riesgos, pero no sustituyen una revisión periódica de seguridad ni garantizan que no pueda ocurrir un incidente.',
        ],
      },
      {
        heading: 'Datos de tarjetas',
        paragraphs: [
          'Gastio permite organizar compras con tarjeta, pero no necesita almacenar el número completo, CVV o PIN. No ingreses datos bancarios secretos en descripciones ni notas.',
        ],
      },
      {
        heading: 'Alojamiento y acceso operativo',
        paragraphs: [
          'El alojamiento permite almacenar y procesar la información necesaria para el servicio. La protección de los datos también depende de los controles de acceso y de la seguridad de las sesiones.',
          'El acceso de soporte o administración se limita a casos justificados y personal autorizado. El tratamiento de datos se describe en la Política de privacidad.',
          'Ninguna plataforma puede garantizar riesgo cero. Protegé tu cuenta y conservá los comprobantes originales de tus operaciones.',
        ],
      },
      {
        heading: 'Vos también podés ayudar',
        paragraphs: [
          'Protegé tu cuenta Google, cerrá sesión en dispositivos compartidos, revisá integrantes y permisos de cada hogar, evitá guardar secretos bancarios en campos de texto y contrastá saldos y vencimientos con tus fuentes originales.',
        ],
      },
      {
        heading: 'Control de tu información',
        paragraphs: [
          'Podés solicitar acceso, actualización, rectificación y, cuando corresponda, eliminación de tus datos personales. Consultá las condiciones en la Política de privacidad.',
        ],
      },
    ],
  },
};

@Component({
  imports: [RouterLink],
  template: `
    <main class="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
      <a href="#document-content" class="sr-only focus:not-sr-only focus:absolute focus:left-5 focus:top-5 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-slate-950">Saltar al contenido</a>
      <header class="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <nav class="mx-auto flex max-w-5xl items-center justify-between px-5 py-4" aria-label="Navegación principal">
          <a routerLink="/" class="flex items-center gap-2 text-lg font-black text-brand-700 dark:text-teal-300"><img src="/branding/favicon.webp" alt="" aria-hidden="true" class="size-8 object-contain" />Gastio</a>
          <a routerLink="/login" class="rounded-xl px-4 py-2 text-sm font-bold hover:bg-slate-100 dark:hover:bg-slate-800">Ingresar</a>
        </nav>
      </header>
      <article id="document-content" class="mx-auto max-w-3xl px-5 py-10 sm:py-16">
        <a routerLink="/" class="text-sm font-bold text-brand-700 hover:underline dark:text-teal-300">← Volver a Gastio</a>
        <header class="mt-8">
          <p class="text-sm font-bold uppercase tracking-[.16em] text-brand-700 dark:text-teal-300">Información pública</p>
          <h1 class="mt-3 text-3xl font-black tracking-tight sm:text-4xl">{{ document.title }}</h1>
          <dl class="mt-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 text-sm sm:grid-cols-3 dark:border-slate-800 dark:bg-slate-900">
            <div><dt class="font-bold text-slate-500 dark:text-slate-400">Versión</dt><dd class="mt-1">{{ document.version }}</dd></div>
            <div><dt class="font-bold text-slate-500 dark:text-slate-400">Fecha del documento</dt><dd class="mt-1">{{ document.preparedDate }}</dd></div>
            <div><dt class="font-bold text-slate-500 dark:text-slate-400">Vigencia</dt><dd class="mt-1">{{ document.effectiveDate }}</dd></div>
          </dl>
        </header>

        <div class="mt-8 space-y-8">
          @for (section of document.sections; track section.heading) {
            <section [attr.aria-labelledby]="'section-' + $index">
              <h2 [id]="'section-' + $index" class="text-xl font-black">{{ section.heading }}</h2>
              @for (paragraph of section.paragraphs; track $index) {
                <p class="mt-3 leading-7 text-slate-700 dark:text-slate-300">{{ paragraph }}</p>
              }
              @if (section.bullets?.length) {
                <ul class="mt-3 list-disc space-y-2 pl-6 leading-7 text-slate-700 dark:text-slate-300">
                  @for (bullet of section.bullets; track $index) { <li>{{ bullet }}</li> }
                </ul>
              }
            </section>
          }
        </div>
        <nav class="mt-12 border-t border-slate-200 pt-6 dark:border-slate-800" aria-label="Otros documentos">
          <h2 class="font-bold">Más información</h2>
          <ul class="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm font-semibold text-brand-700 dark:text-teal-300">
            <li><a routerLink="/terminos" class="hover:underline">Términos</a></li>
            <li><a routerLink="/privacidad" class="hover:underline">Privacidad</a></li>
            <li><a routerLink="/como-funciona" class="hover:underline">Cómo funciona</a></li>
            <li><a routerLink="/seguridad" class="hover:underline">Seguridad</a></li>
          </ul>
        </nav>
      </article>
      <footer class="border-t border-slate-200 bg-white px-5 py-6 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">Gastio · Finanzas familiares claras</footer>
    </main>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PublicInformationPageComponent {
  private readonly route = inject(ActivatedRoute);
  protected readonly document = documents[this.route.snapshot.data['document'] as string] ?? documents['terms'];
}
