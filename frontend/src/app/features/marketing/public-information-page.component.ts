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
  publicationPending: boolean;
  sections: InformationSection[];
}

const documents: Record<string, PublicDocument> = {
  terms: {
    title: 'Términos y condiciones de uso',
    version: '0.1 (borrador)',
    preparedDate: '13 de octubre de 2026',
    effectiveDate: 'No vigente; pendiente de aprobación',
    publicationPending: true,
    sections: [{
      heading: 'Estado de publicación',
      paragraphs: [
        'El texto de términos está en revisión y todavía no constituye una versión vigente. No se publica su contenido hasta completar las confirmaciones operativas y la revisión legal.',
        'La aceptación de una versión se solicitará durante el onboarding una vez que esté aprobada y publicada. No se registra aceptación de este borrador.',
      ],
    }],
  },
  privacy: {
    title: 'Política de privacidad',
    version: '0.1 (borrador)',
    preparedDate: '13 de octubre de 2026',
    effectiveDate: 'No vigente; pendiente de aprobación',
    publicationPending: true,
    sections: [{
      heading: 'Estado de publicación',
      paragraphs: [
        'La política está en revisión. No se publica el texto hasta confirmar, entre otros puntos, la identidad del responsable, proveedores, ubicaciones de almacenamiento, plazos de conservación y canales para ejercer derechos.',
        'Esta página no reemplaza la política de privacidad vigente. El contenido completo se publicará una vez aprobado y verificado.',
      ],
    }],
  },
  howItWorks: {
    title: 'Cómo funciona Gastio',
    version: '0.1 · guía pública',
    preparedDate: 'Octubre de 2026',
    effectiveDate: 'No aplica; guía informativa',
    publicationPending: false,
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
    publicationPending: false,
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
          'La implementación reportada incluye controles CSRF para acciones autenticadas, verificaciones de permisos, transacciones de base de datos, idempotencia para evitar duplicados accidentales y un historial trazable de correcciones y anulaciones.',
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
          'La configuración de producción debe ofrecer HTTPS y cookies de sesión seguras. La configuración desplegada, el proveedor de alojamiento, el país de almacenamiento y las políticas de respaldo y recuperación deben verificarse antes de confirmar sus detalles.',
          'El acceso de soporte o administración debe limitarse a casos justificados y personal autorizado. Los proveedores y sus funciones deben identificarse en la Política de privacidad antes de su publicación.',
          'No se afirma cifrado de base de datos en reposo, auditorías externas, certificaciones ni plazos específicos de recuperación sin comprobar esas medidas. Ninguna plataforma puede garantizar riesgo cero.',
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
          'Podés solicitar acceso, actualización, rectificación y, cuando corresponda, eliminación de tus datos personales. Los canales y condiciones se informarán en la Política de privacidad cuando esté aprobada y publicada.',
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

        @if (document.publicationPending) {
          <p role="status" class="mt-8 rounded-2xl border border-amber-300 bg-amber-50 p-5 leading-7 text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
            El contenido sustantivo de este documento no está publicado porque todavía requiere aprobación y confirmaciones. La versión indicada es un borrador y no está vigente.
          </p>
        }

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
