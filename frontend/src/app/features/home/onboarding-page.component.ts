import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../core/auth.service';

@Component({
  imports: [FormsModule],
  template: `
    <main class="grid min-h-screen place-items-center bg-slate-50 p-5 dark:bg-slate-950">
      <section class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-xl dark:bg-slate-900">
        <p class="text-sm font-bold uppercase tracking-[.16em] text-brand-700 dark:text-teal-300">Primer paso</p>
        <h1 class="mt-3 text-3xl font-black">Creá tu primer hogar</h1>
        <p class="mt-4 text-slate-600 dark:text-slate-300">No creamos hogares automáticamente. Elegí un nombre para comenzar.</p>
        <form class="mt-7 space-y-4" (ngSubmit)="submit()">
          <label class="block font-semibold" for="household-name">Nombre del hogar</label>
          <input id="household-name" name="name" [(ngModel)]="name" maxlength="120" required class="w-full rounded-xl border border-slate-300 px-4 py-3 dark:border-slate-700 dark:bg-slate-800" placeholder="Ej.: Casa familiar" />
          @if (auth.error()) { <p class="text-sm font-semibold text-rose-700 dark:text-rose-300">{{ auth.error() }}</p> }
          <button type="submit" [disabled]="auth.isLoading() || !name.trim()" class="w-full rounded-xl bg-brand-700 px-4 py-3 font-bold text-white disabled:opacity-50">{{ auth.isLoading() ? 'Creando…' : 'Crear hogar' }}</button>
        </form>
      </section>
    </main>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OnboardingPageComponent {
  protected readonly auth = inject(AuthService);
  protected name = '';
  private readonly router = inject(Router);

  protected async submit(): Promise<void> {
    if (await this.auth.createFirstHousehold(this.name.trim())) await this.router.navigateByUrl('/app');
  }
}
