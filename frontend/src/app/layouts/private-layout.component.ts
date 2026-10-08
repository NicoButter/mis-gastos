import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="min-h-screen bg-surface dark:bg-slate-950">
      <header class="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900 lg:hidden">
        <span class="font-black text-brand-700 dark:text-teal-300">Gastio</span>
        <button type="button" class="rounded-lg p-2" (click)="mobileOpen.set(!mobileOpen())" [attr.aria-expanded]="mobileOpen()">Menú</button>
      </header>
      <aside class="fixed inset-y-0 left-0 z-20 w-72 border-r border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900" [class.hidden]="!mobileOpen()" [class.lg:block]="true">
        <div class="flex items-center justify-between"><span class="text-xl font-black text-brand-700 dark:text-teal-300">Gastio</span><button class="lg:hidden" type="button" (click)="mobileOpen.set(false)">Cerrar</button></div>
        <button type="button" class="mt-8 flex w-full items-center justify-between rounded-xl border border-slate-200 px-3 py-3 text-left text-sm dark:border-slate-700"><span><span class="block text-xs text-slate-500">Hogar activo</span>Sin hogar seleccionado</span><span>⌄</span></button>
        <nav class="mt-6 space-y-1" aria-label="Aplicación">
          <a routerLink="dashboard" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block rounded-lg px-3 py-2 font-medium">Panel</a>
          <a routerLink="quick" routerLinkActive="bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-teal-300" class="block rounded-lg px-3 py-2 font-medium">Modo rápido</a>
          <span class="block rounded-lg px-3 py-2 text-slate-400">Movimientos · pronto</span>
          <span class="block rounded-lg px-3 py-2 text-slate-400">Ajustes · pronto</span>
        </nav>
        <div class="absolute inset-x-5 bottom-6 border-t border-slate-200 pt-4 text-sm dark:border-slate-700"><p class="font-semibold">Usuario</p><p class="text-slate-500">Sesión pendiente</p></div>
      </aside>
      <main class="min-h-screen p-5 lg:ml-72 lg:p-10"><router-outlet /></main>
      <nav class="fixed inset-x-0 bottom-0 z-10 flex justify-around border-t border-slate-200 bg-white p-2 text-sm dark:border-slate-800 dark:bg-slate-900 lg:hidden" aria-label="Navegación móvil"><a routerLink="dashboard" class="p-2">Panel</a><a routerLink="quick" class="rounded-lg bg-brand-600 px-4 py-2 font-bold text-white">+ Gasto</a></nav>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PrivateLayoutComponent {
  readonly mobileOpen = signal(false);
}
