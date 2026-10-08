import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  imports: [RouterLink],
  template: `
    <main class="grid min-h-screen place-items-center bg-surface p-5 dark:bg-slate-950">
      <section class="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg dark:bg-slate-900">
        <a routerLink="/" class="text-xl font-black text-brand-700 dark:text-teal-300">Gastio</a>
        <h1 class="mt-8 text-2xl font-bold">Ingreso próximamente</h1>
        <p class="mt-3 text-slate-600 dark:text-slate-300">La autenticación basada en sesión y CSRF se conectará en la siguiente fase aprobada.</p>
        <a routerLink="/" class="mt-8 inline-block rounded-lg bg-brand-600 px-4 py-2 font-semibold text-white">Volver al inicio</a>
      </section>
    </main>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginPageComponent {}
