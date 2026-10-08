import { ChangeDetectionStrategy, Component } from '@angular/core';

import { UiStateComponent } from '../../shared/ui-state.component';

@Component({
  imports: [UiStateComponent],
  template: `
    <header><p class="text-sm font-semibold text-brand-700 dark:text-teal-300">Modo completo</p><h1 class="mt-1 text-3xl font-black">Panel</h1><p class="mt-2 text-slate-600 dark:text-slate-300">Tu hogar activo aparecerá aquí cuando lo selecciones.</p></header>
    <section class="mt-8 grid gap-4 sm:grid-cols-3"><div class="rounded-2xl bg-white p-5 shadow-sm dark:bg-slate-900"><p class="text-sm text-slate-500">Ingresos</p><p class="mt-2 text-2xl font-bold">— ARS</p></div><div class="rounded-2xl bg-white p-5 shadow-sm dark:bg-slate-900"><p class="text-sm text-slate-500">Gastos</p><p class="mt-2 text-2xl font-bold">— ARS</p></div><div class="rounded-2xl bg-white p-5 shadow-sm dark:bg-slate-900"><p class="text-sm text-slate-500">Balance</p><p class="mt-2 text-2xl font-bold">— ARS</p></div></section>
    <div class="mt-6"><gst-ui-state label="Estado vacío" title="Todavía no hay información para mostrar" detail="Los datos financieros y el onboarding se incorporarán en fases posteriores." /></div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardPageComponent {}
