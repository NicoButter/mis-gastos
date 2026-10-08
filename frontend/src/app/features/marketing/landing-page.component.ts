import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

interface Feature {
  title: string;
  description: string;
  icon: string;
}

@Component({
  imports: [RouterLink],
  template: `
    <main class="overflow-hidden bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
      <a href="#contenido" class="sr-only focus:not-sr-only focus:absolute focus:left-5 focus:top-5 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-slate-950">Saltar al contenido</a>
      <header class="border-b border-slate-200/70 bg-slate-50/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
        <nav class="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8" aria-label="Navegación principal">
          <a routerLink="/" class="flex items-center gap-2 text-xl font-black tracking-tight text-brand-700 dark:text-teal-300"><span class="grid size-8 place-items-center rounded-lg bg-brand-600 text-sm text-white" aria-hidden="true">G</span>Gastio</a>
          <div class="hidden items-center gap-6 text-sm font-semibold text-slate-600 dark:text-slate-300 md:flex"><a href="#inicio" class="hover:text-brand-700 dark:hover:text-teal-300">Inicio</a><a href="#funcionalidades" class="hover:text-brand-700 dark:hover:text-teal-300">Funcionalidades</a><a href="#como-funciona" class="hover:text-brand-700 dark:hover:text-teal-300">Cómo funciona</a><a href="#preguntas" class="hover:text-brand-700 dark:hover:text-teal-300">Preguntas frecuentes</a></div>
          <div class="hidden items-center gap-2 sm:flex"><a routerLink="/login" class="rounded-xl px-4 py-2 text-sm font-bold hover:bg-slate-200 dark:hover:bg-slate-800">Ingresar</a><a routerLink="/login" class="rounded-xl bg-brand-600 px-4 py-2 text-sm font-bold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-brand-700">Comenzar</a></div>
          <button type="button" class="rounded-lg p-2 md:hidden" (click)="menuOpen.set(!menuOpen())" [attr.aria-expanded]="menuOpen()" aria-controls="public-menu"><span class="sr-only">Abrir menú</span><span aria-hidden="true">☰</span></button>
        </nav>
        @if (menuOpen()) { <div id="public-menu" class="border-t border-slate-200 px-5 py-4 md:hidden dark:border-slate-800"><div class="grid gap-3 text-sm font-semibold"><a href="#funcionalidades" (click)="menuOpen.set(false)">Funcionalidades</a><a href="#como-funciona" (click)="menuOpen.set(false)">Cómo funciona</a><a href="#preguntas" (click)="menuOpen.set(false)">Preguntas frecuentes</a><a routerLink="/login" class="mt-2 rounded-xl bg-brand-600 px-4 py-3 text-center text-white">Comenzar</a></div></div> }
      </header>

      <section id="inicio" class="relative isolate" aria-labelledby="hero-title">
        <div class="absolute inset-x-0 top-0 -z-10 h-[32rem] bg-[radial-gradient(circle_at_top_right,_#ccfbf1,_transparent_50%),radial-gradient(circle_at_top_left,_#dbeafe,_transparent_45%)] dark:bg-[radial-gradient(circle_at_top_right,_#134e4a,_transparent_45%),radial-gradient(circle_at_top_left,_#172554,_transparent_50%)]"></div>
        <div id="contenido" class="mx-auto grid max-w-7xl gap-12 px-5 py-20 lg:grid-cols-[1.05fr_.95fr] lg:items-center lg:px-8 lg:py-28">
          <div><p class="inline-flex rounded-full border border-teal-200 bg-white/70 px-3 py-1 text-xs font-bold tracking-wide text-brand-700 dark:border-teal-800 dark:bg-slate-900/70 dark:text-teal-300">FINANZAS DEL HOGAR, SIN RUIDO</p><h1 id="hero-title" class="mt-6 max-w-3xl text-4xl font-black tracking-[-.04em] sm:text-5xl lg:text-6xl">Tomá el control de tu dinero, <span class="text-brand-700 dark:text-teal-300">sin complicaciones.</span></h1><p class="mt-6 max-w-2xl text-lg leading-8 text-slate-600 dark:text-slate-300">Organizá los ingresos, gastos y presupuestos de tu hogar desde un solo lugar. Simple, claro y pensado para toda la familia.</p><div class="mt-8 flex flex-wrap gap-3"><a routerLink="/login" class="rounded-xl bg-brand-600 px-5 py-3 font-bold text-white shadow-lg shadow-teal-950/10 transition hover:-translate-y-0.5 hover:bg-brand-700">Comenzar <span aria-hidden="true">→</span></a><a href="#funcionalidades" class="rounded-xl border border-slate-300 bg-white px-5 py-3 font-bold shadow-sm transition hover:border-brand-600 dark:border-slate-700 dark:bg-slate-900">Conocer funcionalidades</a></div><p class="mt-6 text-sm text-slate-500">Gastio está en construcción por Vetrabyte. Las funciones financieras se incorporarán por etapas.</p></div>
          <div class="relative mx-auto w-full max-w-lg"><div class="absolute -inset-6 -z-10 rounded-[2.5rem] bg-teal-300/25 blur-3xl dark:bg-teal-500/15"></div><div class="rounded-[2rem] border border-white/80 bg-white p-5 shadow-2xl shadow-slate-900/10 dark:border-slate-700 dark:bg-slate-900"><div class="flex items-center justify-between"><div><p class="text-xs font-semibold text-slate-500">Vista de ejemplo</p><p class="font-bold">Hogar en orden</p></div><span class="rounded-full bg-teal-50 px-3 py-1 text-xs font-bold text-brand-700 dark:bg-teal-950 dark:text-teal-300">Próximamente</span></div><div class="mt-6 grid grid-cols-3 gap-3"><div class="rounded-2xl bg-slate-100 p-3 dark:bg-slate-800"><p class="text-xs text-slate-500">Ingresos</p><p class="mt-1 font-bold">— ARS</p></div><div class="rounded-2xl bg-slate-100 p-3 dark:bg-slate-800"><p class="text-xs text-slate-500">Gastos</p><p class="mt-1 font-bold">— ARS</p></div><div class="rounded-2xl bg-brand-50 p-3 text-brand-700 dark:bg-teal-950 dark:text-teal-300"><p class="text-xs">Balance</p><p class="mt-1 font-bold">— ARS</p></div></div><div class="mt-5 rounded-2xl border border-dashed border-slate-300 p-5 text-sm text-slate-500 dark:border-slate-700">Una representación visual: no contiene ni persiste movimientos.</div></div></div>
        </div>
      </section>

      <section id="funcionalidades" class="mx-auto max-w-7xl px-5 py-20 lg:px-8" aria-labelledby="features-title"><div class="max-w-2xl"><p class="text-sm font-bold uppercase tracking-[.16em] text-brand-700 dark:text-teal-300">Todo en perspectiva</p><h2 id="features-title" class="mt-3 text-3xl font-black tracking-tight sm:text-4xl">Una base clara para las finanzas de cada hogar.</h2><p class="mt-4 text-slate-600 dark:text-slate-300">Estas capacidades están planificadas para las próximas fases. La base técnica y de aislamiento ya está preparada.</p></div><div class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">@for (feature of features; track feature.title) { <article class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"><span class="grid size-10 place-items-center rounded-xl bg-brand-50 text-lg dark:bg-teal-950" aria-hidden="true">{{ feature.icon }}</span><div class="mt-5 flex items-start justify-between gap-3"><h3 class="font-bold">{{ feature.title }}</h3><span class="shrink-0 rounded-full bg-slate-100 px-2 py-1 text-[.65rem] font-bold uppercase tracking-wide text-slate-500 dark:bg-slate-800">Planificado</span></div><p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ feature.description }}</p></article> }</div></section>

      <section id="como-funciona" class="border-y border-slate-200 bg-white py-20 dark:border-slate-800 dark:bg-slate-900" aria-labelledby="how-title"><div class="mx-auto max-w-7xl px-5 lg:px-8"><div class="max-w-2xl"><p class="text-sm font-bold uppercase tracking-[.16em] text-brand-700 dark:text-teal-300">Un camino simple</p><h2 id="how-title" class="mt-3 text-3xl font-black tracking-tight sm:text-4xl">Menos fricción para entender tus finanzas.</h2></div><ol class="mt-10 grid gap-5 md:grid-cols-4">@for (step of steps; track step.title; let index = $index) { <li class="relative rounded-2xl bg-slate-50 p-6 dark:bg-slate-950"><span class="text-4xl font-black text-teal-200 dark:text-teal-900">0{{ index + 1 }}</span><h3 class="mt-7 font-bold">{{ step.title }}</h3><p class="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ step.description }}</p></li> }</ol></div></section>

      <section class="mx-auto grid max-w-7xl gap-10 px-5 py-20 lg:grid-cols-2 lg:items-center lg:px-8" aria-labelledby="mobile-title"><div><p class="text-sm font-bold uppercase tracking-[.16em] text-brand-700 dark:text-teal-300">Diseñado para el día a día</p><h2 id="mobile-title" class="mt-3 text-3xl font-black tracking-tight sm:text-4xl">Una experiencia rápida también desde el celular.</h2><p class="mt-5 max-w-xl leading-7 text-slate-600 dark:text-slate-300">El modo rápido está pensado para que registrar un gasto cotidiano requiera pocas decisiones. Será la misma plataforma y los mismos permisos, adaptados a la pantalla que usás.</p><a routerLink="/login" class="mt-7 inline-flex font-bold text-brand-700 hover:text-brand-600 dark:text-teal-300">Ver el estado de acceso <span class="ml-2" aria-hidden="true">→</span></a></div><div class="mx-auto rounded-[2.7rem] border-8 border-slate-900 bg-slate-900 p-2 shadow-2xl"><div class="w-64 rounded-[2rem] bg-slate-50 p-4 text-slate-950"><div class="mx-auto h-1.5 w-20 rounded-full bg-slate-300"></div><p class="mt-7 text-xs font-bold text-slate-500">MODO RÁPIDO · VISTA FUTURA</p><h3 class="mt-2 text-xl font-black">¿Qué registramos?</h3><div class="mt-5 rounded-xl border border-slate-200 bg-white p-4"><p class="text-xs text-slate-500">Monto</p><p class="mt-1 text-2xl font-black">— ARS</p></div><div class="mt-3 grid gap-2"><div class="rounded-xl bg-white p-3 text-sm font-semibold shadow-sm">Categoría</div><div class="rounded-xl bg-white p-3 text-sm font-semibold shadow-sm">Cuenta</div></div><button type="button" disabled class="mt-5 w-full rounded-xl bg-slate-300 py-3 text-sm font-bold text-slate-500">Guardar · próximamente</button></div></div></section>

      <section id="preguntas" class="bg-slate-100 py-20 dark:bg-slate-900" aria-labelledby="faq-title"><div class="mx-auto max-w-3xl px-5"><p class="text-center text-sm font-bold uppercase tracking-[.16em] text-brand-700 dark:text-teal-300">Preguntas frecuentes</p><h2 id="faq-title" class="mt-3 text-center text-3xl font-black tracking-tight sm:text-4xl">Lo esencial, sin letra chica.</h2><div class="mt-10 space-y-3">@for (faq of faqs; track faq.question) { <details class="rounded-2xl bg-white p-5 shadow-sm dark:bg-slate-950"><summary class="cursor-pointer font-bold">{{ faq.question }}</summary><p class="mt-3 pr-8 text-sm leading-6 text-slate-600 dark:text-slate-300">{{ faq.answer }}</p></details> }</div></div></section>

      <footer class="bg-slate-950 px-5 py-12 text-slate-300"><div class="mx-auto flex max-w-7xl flex-col gap-8 sm:flex-row sm:items-end sm:justify-between lg:px-3"><div><p class="text-xl font-black text-white">Gastio</p><p class="mt-2 max-w-md text-sm leading-6">Organizá tus gastos. Viví con tranquilidad.</p></div><div class="flex flex-wrap gap-x-5 gap-y-2 text-sm"><a href="#inicio" class="hover:text-white">Inicio</a><a href="#preguntas" class="hover:text-white">Preguntas frecuentes</a><span class="cursor-not-allowed text-slate-500" aria-label="Política de privacidad próximamente">Privacidad · próximamente</span><span class="cursor-not-allowed text-slate-500" aria-label="Términos de servicio próximamente">Términos · próximamente</span></div></div><p class="mx-auto mt-10 max-w-7xl border-t border-slate-800 pt-5 text-xs text-slate-500 lg:px-3">Una iniciativa de Vetrabyte.</p></footer>
    </main>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LandingPageComponent {
  readonly menuOpen = signal(false);
  readonly features: Feature[] = [
    { icon: '↗', title: 'Ingresos y gastos', description: 'Registrá y comprendé el movimiento de tu dinero.' },
    { icon: '◫', title: 'Cuentas organizadas', description: 'Separá efectivo, bancos y billeteras en un mismo panorama.' },
    { icon: '◎', title: 'Hogar compartido', description: 'Coordiná la información financiera con quienes conviven con vos.' },
    { icon: '◌', title: 'Tarjetas y cuotas', description: 'Visualizá compromisos futuros sin duplicar consumos.' },
    { icon: '▥', title: 'Presupuestos mensuales', description: 'Planificá por categoría y seguí el progreso con claridad.' },
    { icon: '⌁', title: 'Informes y estadísticas', description: 'Convertí registros cotidianos en decisiones más informadas.' },
    { icon: '⚡', title: 'Registro rápido móvil', description: 'Preparado para cargar gastos diarios desde tu celular.' },
  ];
  readonly steps = [
    { title: 'Creá tu cuenta', description: 'Accedé de forma segura cuando la autenticación esté disponible.' },
    { title: 'Organizá tu hogar', description: 'Definí el espacio compartido para administrar tus finanzas.' },
    { title: 'Registrá movimientos', description: 'Capturá lo importante de forma simple y contextual.' },
    { title: 'Comprendé y planificá', description: 'Usá la información para decidir con más tranquilidad.' },
  ];
  readonly faqs = [
    { question: '¿Gastio ya permite registrar gastos?', answer: 'La plataforma está preparando su base técnica. Las operaciones financieras se habilitarán de manera progresiva en próximas fases.' },
    { question: '¿Puedo compartir un hogar?', answer: 'El modelo de hogares y membresías ya contempla colaboración. La interfaz de invitaciones llegará junto a la autenticación.' },
    { question: '¿Necesito instalar una aplicación?', answer: 'Gastio está pensado como una experiencia web responsive, con una base preparada para convertirse en PWA online.' },
  ];
}
