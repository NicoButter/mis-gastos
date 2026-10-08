import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  imports: [RouterLink],
  template: `<main class="grid min-h-screen place-items-center bg-slate-50 p-6 text-center dark:bg-slate-950"><section class="max-w-lg"><p class="text-7xl font-black text-brand-600">404</p><h1 class="mt-5 text-3xl font-black">Esta página no está en tu presupuesto.</h1><p class="mt-4 text-slate-600 dark:text-slate-300">La dirección no existe o fue movida. Podés volver a la portada de Gastio.</p><a routerLink="/" class="mt-8 inline-flex rounded-xl bg-brand-600 px-5 py-3 font-bold text-white">Volver al inicio</a></section></main>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotFoundPageComponent {}
