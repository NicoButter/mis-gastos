import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth.service';

@Component({
  imports: [FormsModule, RouterLink],
  template: `
    <main class="grid min-h-screen place-items-center bg-slate-50 p-5 dark:bg-slate-950">
      <section class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-xl dark:bg-slate-900">
        <p class="text-sm font-bold uppercase tracking-[.16em] text-brand-700 dark:text-teal-300">Primer paso</p>
        <h1 class="mt-3 text-3xl font-black">Creá tu primer hogar</h1>
        <p class="mt-4 text-slate-600 dark:text-slate-300">No creamos hogares automáticamente. Elegí un nombre para comenzar.</p>
        <form class="mt-7 space-y-4" (ngSubmit)="submit()">
          <label class="block font-semibold" for="household-name">Nombre del hogar</label>
          <input id="household-name" name="name" [(ngModel)]="name" maxlength="120" required class="w-full rounded-xl border border-slate-300 px-4 py-3 dark:border-slate-700 dark:bg-slate-800" placeholder="Ej.: Casa familiar" />
          @if (auth.termsVersion()) {
            <label for="accept-terms" class="flex items-start gap-3 text-sm leading-6 text-slate-700 dark:text-slate-300">
              <input id="accept-terms" name="acceptTerms" type="checkbox" [(ngModel)]="acceptTerms" required class="mt-1 size-4 accent-teal-700" />
              <span>Leí y acepto los <a routerLink="/terminos" class="font-bold text-brand-700 underline dark:text-teal-300">Términos y condiciones</a> versión {{ auth.termsVersion() }}. También puedo consultar la <a routerLink="/privacidad" class="font-bold text-brand-700 underline dark:text-teal-300">Política de privacidad</a>.</span>
            </label>
          } @else {
            <p class="text-sm leading-6 text-slate-600 dark:text-slate-300">Consultá los <a routerLink="/terminos" class="font-bold text-brand-700 underline dark:text-teal-300">Términos y condiciones</a> y la <a routerLink="/privacidad" class="font-bold text-brand-700 underline dark:text-teal-300">Política de privacidad</a> de Mis Gastos.</p>
          }
          @if (auth.error()) { <p class="text-sm font-semibold text-rose-700 dark:text-rose-300">{{ auth.error() }}</p> }
          <button type="submit" [disabled]="auth.isLoading() || !name.trim() || (!!auth.termsVersion() && !acceptTerms)" class="w-full rounded-xl bg-brand-700 px-4 py-3 font-bold text-white disabled:opacity-50">{{ auth.isLoading() ? 'Creando…' : 'Crear hogar' }}</button>
        </form>
      </section>
    </main>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OnboardingPageComponent {
  protected readonly auth = inject(AuthService);
  protected name = '';
  protected acceptTerms = false;
  private readonly router = inject(Router);

  protected async submit(): Promise<void> {
    const termsVersion = this.auth.termsVersion();
    if (termsVersion && !this.acceptTerms) return;
    if (await this.auth.createFirstHousehold(this.name.trim(), termsVersion ?? undefined)) {
      await this.router.navigateByUrl('/app');
    }
  }
}
