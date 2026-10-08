import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../core/auth.service';

@Component({
  selector: 'gst-private-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="min-h-screen bg-surface dark:bg-slate-950">
      <header class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900 lg:hidden">
        <span class="font-black text-brand-700 dark:text-teal-300">Gastio</span>
        <button type="button" class="rounded-lg p-2" (click)="mobileOpen.set(!mobileOpen())" [attr.aria-expanded]="mobileOpen()">Menú</button>
      </header>
      <aside class="fixed inset-y-0 left-0 z-20 w-72 border-r border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900" [class.hidden]="!mobileOpen()" [class.lg:block]="true">
        <div class="flex items-center justify-between"><span class="text-xl font-black text-brand-700 dark:text-teal-300">Gastio</span><button class="lg:hidden" type="button" (click)="mobileOpen.set(false)">Cerrar</button></div>
        <label class="mt-8 block text-xs font-semibold text-slate-500" for="active-household">Hogar activo</label><select id="active-household" class="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm dark:border-slate-700 dark:bg-slate-900" [value]="auth.activeHousehold()?.id ?? ''" (change)="selectHousehold($any($event.target).value)"><option value="" disabled>Seleccioná un hogar</option>@for (household of auth.households(); track household.id) { <option [value]="household.id">{{ household.name }}</option> }</select>
        <nav class="mt-6 space-y-1" aria-label="Aplicación">
          <a routerLink="/app" [routerLinkActiveOptions]="{ exact: true }" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block rounded-lg px-3 py-2 font-medium">Panel</a>
          <a routerLink="quick" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block rounded-lg px-3 py-2 font-medium">Modo rápido</a>
          <a routerLink="transactions" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block rounded-lg px-3 py-2 font-medium">Movimientos</a>
          <a routerLink="accounts" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block rounded-lg px-3 py-2 font-medium">Cuentas</a>
          <a routerLink="households" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block rounded-lg px-3 py-2 font-medium">Hogares</a>
          <a routerLink="settings" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block rounded-lg px-3 py-2 font-medium">Configuración</a>
        </nav>
        <div class="absolute inset-x-5 bottom-6 border-t border-slate-200 pt-4 text-sm dark:border-slate-700"><p class="font-semibold">{{ auth.currentUser()?.displayName }}</p><p class="text-slate-500">{{ auth.currentUser()?.email }}</p><button type="button" (click)="logout()" class="mt-3 font-semibold text-brand-700 dark:text-teal-300">Cerrar sesión</button></div>
      </aside>
      <main class="min-h-screen p-5 lg:ml-72 lg:p-10"><router-outlet /></main>
      <nav class="fixed inset-x-0 bottom-0 z-10 flex justify-around border-t border-slate-200 bg-white p-2 text-sm dark:border-slate-800 dark:bg-slate-900 lg:hidden" aria-label="Navegación móvil"><a routerLink="/app" class="p-2">Panel</a><a routerLink="quick" class="rounded-lg bg-brand-600 px-4 py-2 font-bold text-white">+ Gasto</a></nav>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PrivateLayoutComponent {
  readonly mobileOpen = signal(false);
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected async logout(): Promise<void> {
    await this.auth.logout();
    if (!this.auth.isAuthenticated()) await this.router.navigateByUrl('/');
  }

  protected async selectHousehold(householdId: string): Promise<void> {
    if (householdId) await this.auth.selectHousehold(householdId);
  }
}
