import { ChangeDetectionStrategy, Component, HostListener, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../core/auth.service';

@Component({
  selector: 'gst-private-layout',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="min-h-screen bg-surface dark:bg-slate-950">
      <header class="app-header flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900 lg:justify-start lg:gap-3" [class.desktop-sidebar-open]="!desktopCollapsed()">
        <span class="font-black text-brand-700 dark:text-teal-300">Gastio</span>
        <button type="button" class="sidebar-toggle lg:hidden" (click)="mobileOpen.set(!mobileOpen())" aria-controls="app-sidebar" [attr.aria-expanded]="mobileOpen()" [attr.aria-label]="mobileOpen() ? 'Cerrar menú' : 'Abrir menú'" title="Menú">
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M9 4v16" /></svg>
        </button>
        <button type="button" class="sidebar-toggle hidden lg:order-first lg:inline-flex" (click)="toggleDesktopSidebar()" aria-controls="app-sidebar" [attr.aria-expanded]="!desktopCollapsed()" aria-label="Mostrar barra lateral" title="Mostrar barra lateral">
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M9 4v16m4 5 3 3-3 3" /></svg>
        </button>
      </header>
      <button type="button" class="sidebar-backdrop fixed inset-0 z-20 bg-slate-950/40 lg:hidden" [class.is-open]="mobileOpen()" aria-label="Cerrar menú" (click)="mobileOpen.set(false)"></button>
      <aside id="app-sidebar" class="app-sidebar fixed inset-y-0 left-0 z-30 w-72 max-w-full overflow-y-auto border-r border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900" [class.mobile-open]="mobileOpen()" [class.desktop-collapsed]="desktopCollapsed()">
        <div class="flex items-center justify-between">
          <span class="text-xl font-black text-brand-700 dark:text-teal-300">Gastio</span>
          <button class="sidebar-toggle lg:hidden" type="button" (click)="mobileOpen.set(false)" aria-controls="app-sidebar" aria-expanded="true" aria-label="Cerrar menú" title="Cerrar menú">
            <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="m6 6 12 12M6 18 18 6" /></svg>
          </button>
          <button class="sidebar-toggle hidden lg:inline-flex" type="button" (click)="toggleDesktopSidebar()" aria-controls="app-sidebar" [attr.aria-expanded]="!desktopCollapsed()" aria-label="Ocultar barra lateral" title="Ocultar barra lateral">
            <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M9 4v16m7-11-3 3 3 3" /></svg>
          </button>
        </div>
        <label class="mt-8 block text-xs font-semibold text-slate-500" for="active-household">Hogar activo</label><select id="active-household" class="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-3 text-sm dark:border-slate-700 dark:bg-slate-900" [value]="auth.activeHousehold()?.id ?? ''" (change)="selectHousehold($any($event.target).value)"><option value="" disabled>Seleccioná un hogar</option>@for (household of auth.households(); track household.id) { <option [value]="household.id">{{ household.name }}</option> }</select>
        <nav (click)="mobileOpen.set(false)" class="mt-6 space-y-1" aria-label="Aplicación">
          <a routerLink="/app" [routerLinkActiveOptions]="{ exact: true }" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Panel</a>
          <a routerLink="quick" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Modo rápido</a>
          <a routerLink="transactions" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Movimientos</a>
          <a routerLink="accounts" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Cuentas</a>
          <a routerLink="cards" routerLinkActive="bg-brand-50 text-brand-700" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Tarjetas</a>
          <a routerLink="installments" routerLinkActive="bg-brand-50 text-brand-700" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Compras en cuotas</a>
          <a routerLink="recurring" routerLinkActive="bg-brand-50 text-brand-700" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Gastos recurrentes</a>
          <a routerLink="categories" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Categorías</a>
          <a routerLink="households" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Hogares</a>
          <a routerLink="settings" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block min-h-11 rounded-lg px-3 py-3 font-medium">Configuración</a>
        </nav>
        @if (auth.currentUser(); as user) {
          <div class="mt-8 border-t border-slate-200 pt-4 text-sm dark:border-slate-700">
            <div class="flex items-center gap-3">
              <span class="relative grid size-10 shrink-0 place-items-center overflow-hidden rounded-full bg-brand-100 font-bold text-brand-700 dark:bg-slate-800 dark:text-teal-300" aria-hidden="true">
                {{ initials(user.displayName) }}
                @if (user.avatarUrl) { <img [src]="user.avatarUrl" [alt]="'Foto de ' + user.displayName" class="absolute inset-0 size-full object-cover" (error)="$any($event.target).remove()" /> }
              </span>
              <div class="min-w-0"><p class="truncate font-semibold">{{ user.displayName }}</p><p class="truncate text-slate-500">{{ user.email }}</p></div>
            </div>
            <button type="button" (click)="logout()" class="mt-3 font-semibold text-brand-700 dark:text-teal-300">Cerrar sesión</button>
          </div>
        }
      </aside>
      <main class="app-content min-h-screen p-5 pb-24 lg:p-10" [class.lg:ml-72]="!desktopCollapsed()"><router-outlet /></main>
      <nav class="fixed inset-x-0 bottom-0 z-10 flex justify-around border-t border-slate-200 bg-white p-2 text-sm dark:border-slate-800 dark:bg-slate-900 lg:hidden" aria-label="Navegación móvil"><a routerLink="/app" class="p-2 min-h-11 inline-flex items-center">Panel</a><a routerLink="quick" class="rounded-lg bg-brand-600 px-4 py-2 min-h-11 inline-flex items-center font-bold text-white">+ Gasto</a></nav>
    </div>
  `,
  styles: `
    .sidebar-toggle { align-items: center; justify-content: center; min-width: 44px; min-height: 44px; border-radius: .75rem; }
    .sidebar-toggle:hover { background: light-dark(#f1f5f9, #1e293b); }
    .app-sidebar {
      transform: translateX(-100%);
      visibility: hidden;
      pointer-events: none;
      transition: transform 260ms cubic-bezier(.22, 1, .36, 1), visibility 0s 260ms;
    }
    .app-sidebar.mobile-open { transform: translateX(0); visibility: visible; pointer-events: auto; transition-delay: 0s; }
    .sidebar-backdrop { opacity: 0; visibility: hidden; pointer-events: none; transition: opacity 260ms ease, visibility 0s 260ms; }
    .sidebar-backdrop.is-open { opacity: 1; visibility: visible; pointer-events: auto; transition-delay: 0s; }
    .app-content { transition: margin-left 260ms cubic-bezier(.22, 1, .36, 1); }
    @media (min-width: 1024px) {
      .app-sidebar { transform: translateX(0); visibility: visible; pointer-events: auto; transition-delay: 0s; }
      .app-sidebar.desktop-collapsed { transform: translateX(-100%); visibility: hidden; pointer-events: none; transition-delay: 0s, 260ms; }
      .app-header { max-height: 80px; opacity: 1; overflow: hidden; visibility: visible; transition: max-height 260ms cubic-bezier(.22, 1, .36, 1), padding 260ms cubic-bezier(.22, 1, .36, 1), opacity 260ms ease, visibility 0s; }
      .app-header.desktop-sidebar-open { max-height: 0; padding-block: 0; border-bottom-width: 0; opacity: 0; visibility: hidden; transition-delay: 0s, 0s, 0s, 260ms; }
    }
    @media (prefers-reduced-motion: reduce) {
      .app-sidebar, .sidebar-backdrop, .app-content, .app-header { transition: none; }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PrivateLayoutComponent {
  readonly mobileOpen = signal(false);
  readonly desktopCollapsed = signal(this.readSidebarPreference());
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected toggleDesktopSidebar(): void {
    this.desktopCollapsed.update((collapsed) => !collapsed);
    try {
      localStorage.setItem('gastio.sidebar.collapsed', String(this.desktopCollapsed()));
    } catch {
      // The sidebar remains usable when browser storage is unavailable.
    }
  }

  @HostListener('document:keydown.escape')
  protected closeMobileSidebar(): void {
    this.mobileOpen.set(false);
  }

  private readSidebarPreference(): boolean {
    try {
      return localStorage.getItem('gastio.sidebar.collapsed') === 'true';
    } catch {
      return false;
    }
  }

  protected async logout(): Promise<void> {
    await this.auth.logout();
    if (!this.auth.isAuthenticated()) await this.router.navigateByUrl('/');
  }

  protected async selectHousehold(householdId: string): Promise<void> {
    if (householdId) await this.auth.selectHousehold(householdId);
  }

  protected initials(displayName: string): string {
    return displayName
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('');
  }
}
