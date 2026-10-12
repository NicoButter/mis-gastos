import { ChangeDetectionStrategy, Component } from '@angular/core';

import { OperationFormComponent } from '../finance/operation-form.component';

@Component({
  imports: [OperationFormComponent],
  template: `
    <div class="mx-auto w-full max-w-lg">
      <header class="mb-6">
        <p class="inline-flex items-center gap-2 text-sm font-semibold text-brand-700 dark:text-teal-300">
          <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="m13 2-9 12h7l-1 8 10-12h-7l1-8Z" /></svg>
          Modo rápido
        </p>
        <h1 class="mt-2 text-3xl font-bold tracking-tight">Registrar un gasto</h1>
        <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">¿Cuánto gastaste? Elegí la categoría y guardalo.</p>
      </header>
      <section class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-7" aria-label="Gasto rápido">
        <gst-operation-form [quick]="true" />
      </section>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class QuickModePageComponent {}
