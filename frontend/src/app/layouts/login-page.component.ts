import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../core/auth.service';

@Component({
  imports: [RouterLink],
  template: `
    <main class="grid min-h-screen place-items-center bg-slate-50 p-5 dark:bg-slate-950">
      <section class="grid w-full max-w-4xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/10 md:grid-cols-[.9fr_1.1fr] dark:border-slate-800 dark:bg-slate-900">
        <aside class="hidden bg-brand-700 p-10 text-white md:flex md:flex-col"><a routerLink="/" class="text-xl font-black">Gastio</a><div class="my-auto"><p class="text-sm font-bold uppercase tracking-[.16em] text-teal-200">Bienvenido</p><h1 class="mt-4 text-4xl font-black tracking-tight">Un lugar claro para las finanzas de tu hogar.</h1><p class="mt-5 leading-7 text-teal-50">Accedé de forma segura con tu cuenta Google.</p></div><p class="text-sm text-teal-100">Una iniciativa de Vetrabyte.</p></aside>
        <div class="p-7 sm:p-10"><a routerLink="/" class="inline-flex items-center gap-2 text-sm font-bold text-brand-700 dark:text-teal-300"><span aria-hidden="true">←</span> Volver a la landing</a><div class="mt-12"><p class="text-sm font-bold uppercase tracking-[.16em] text-brand-700 dark:text-teal-300">Acceso</p><h2 class="mt-3 text-3xl font-black">Ingresá a Gastio</h2><p class="mt-4 leading-7 text-slate-600 dark:text-slate-300">Tu sesión es administrada por Gastio mediante cookies seguras; nunca almacenamos tokens de acceso en el navegador.</p><button type="button" (click)="login()" [disabled]="auth.isLoading() || !auth.googleLoginEnabled()" aria-describedby="google-help" class="mt-8 flex w-full items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 font-bold text-slate-700 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"><span class="grid size-5 place-items-center rounded-full bg-white text-xs shadow-sm">G</span>Continuar con Google</button><p id="google-help" class="mt-3 text-center text-xs leading-5 text-slate-500">@if (!auth.googleLoginEnabled()) { Google OAuth no está configurado en este entorno. } @else { Serás redirigido a Google para autenticarte. }</p><div class="mt-8 rounded-xl border border-dashed border-slate-300 p-4 text-sm text-slate-500 dark:border-slate-700">@if (auth.isLoading()) { <p class="font-semibold text-slate-700 dark:text-slate-200">Comprobando sesión…</p> } @else if (message) { <p class="font-semibold text-rose-700 dark:text-rose-300">{{ message }}</p> } @else if (auth.error()) { <p class="font-semibold text-rose-700 dark:text-rose-300">{{ auth.error() }}</p> } @else { <p class="font-semibold text-slate-700 dark:text-slate-200">Estado de sesión: sin sesión activa</p><p class="mt-1">Podés continuar con Google para ingresar.</p> }</div></div></div>
      </section>
    </main>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginPageComponent {
  protected readonly auth = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  protected readonly message = this.errorMessage(this.route.snapshot.queryParamMap.get('error'));

  protected async login(): Promise<void> {
    if (this.auth.isAuthenticated()) {
      await this.router.navigateByUrl(this.route.snapshot.queryParamMap.get('returnUrl') || '/app');
      return;
    }
    await this.auth.startGoogleLogin();
  }

  private errorMessage(code: string | null): string | null {
    if (code === 'account_link_required') return 'Esta cuenta ya existe. Contactá a soporte para vincular Google de forma segura.';
    if (code === 'oauth_failed') return 'Google no pudo completar el acceso. Revisá la cuenta e intentá nuevamente.';
    return null;
  }
}
