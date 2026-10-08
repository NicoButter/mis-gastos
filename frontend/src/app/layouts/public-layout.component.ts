import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  imports: [RouterLink],
  template: `
    <main class="min-h-screen bg-surface px-5 py-8 dark:bg-slate-950">
      <nav class="mx-auto flex max-w-6xl items-center justify-between" aria-label="Principal">
        <a routerLink="/" class="text-xl font-black tracking-tight text-brand-700 dark:text-teal-300">Gastio</a>
        <a routerLink="/auth/login" class="rounded-lg px-4 py-2 text-sm font-semibold hover:bg-slate-200 dark:hover:bg-slate-800">Ingresar</a>
      </nav>
      <section class="mx-auto grid max-w-6xl gap-10 py-20 lg:grid-cols-2 lg:items-center">
        <div>
          <p class="text-sm font-bold uppercase tracking-[.18em] text-brand-700 dark:text-teal-300">Finanzas del hogar</p>
          <h1 class="mt-4 text-4xl font-black tracking-tight sm:text-5xl">Tu plata, clara. Tu hogar, conectado.</h1>
          <p class="mt-5 max-w-xl text-lg leading-8 text-slate-600 dark:text-slate-300">Gastio prepara un espacio simple y privado para organizar las finanzas familiares.</p>
          <a routerLink="/auth/login" class="mt-8 inline-flex rounded-xl bg-brand-600 px-5 py-3 font-bold text-white shadow-sm hover:bg-brand-700">Comenzar</a>
        </div>
        <aside class="rounded-3xl border border-teal-100 bg-white p-8 shadow-xl dark:border-slate-700 dark:bg-slate-900">
          <p class="font-bold text-brand-700 dark:text-teal-300">Base de producto</p>
          <ul class="mt-4 space-y-3 text-slate-600 dark:text-slate-300"><li>• Hogares aislados por servidor</li><li>• Experiencia completa y modo rápido</li><li>• Diseño responsive y accesible</li></ul>
        </aside>
      </section>
    </main>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PublicLayoutComponent {}
