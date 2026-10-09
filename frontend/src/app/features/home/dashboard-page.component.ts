import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { FinanceService, Summary, financeError, localDate, money } from '../../core/finance.service';

@Component({
  imports: [FormsModule, RouterLink],
  template: `
    <header class="flex flex-wrap justify-between gap-4"><div><p class="text-sm font-semibold text-brand-700">{{ auth.activeHousehold()?.name || 'Seleccioná un hogar' }}</p><h1 class="text-3xl font-black mt-1">Panel financiero</h1></div><a routerLink="/app/quick" class="btn-primary">+ Gasto rápido</a></header>
    <label class="block mt-5 max-w-xs">Mes<input class="form-input" type="month" [(ngModel)]="month" (ngModelChange)="load()"></label>
    @if (error()) { <p class="notice-error" role="alert">{{ error() }}</p><button class="underline" (click)="load()">Reintentar</button> }
    @if (loading()) { <p class="mt-6" role="status">Cargando resumen…</p> }
    @if (summary(); as data) {
      <section class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">@for (item of kpis(data); track item.label) { <article class="finance-card"><p class="text-sm text-slate-500">{{ item.label }}</p><p class="mt-2 text-2xl font-black">{{ money(item.value) }}</p><p class="text-xs mt-1">ARS</p></article> }</section>
      <p class="mt-3 text-sm text-slate-500">{{ data.count }} movimientos del mes. El saldo consolidado incluye cuentas archivadas.</p>
      <section class="mt-6 grid gap-6 xl:grid-cols-2"><article class="finance-card"><h2 class="text-xl font-bold">Cuentas y saldos</h2>@for (account of data.accounts; track account.id) { <a routerLink="/app/transactions" [queryParams]="{account: account.id}" class="flex flex-wrap justify-between gap-2 border-b py-4"><span>{{ account.name }}{{ account.is_active ? '' : ' · Archivada' }}</span><strong>{{ money(account.balance) }}</strong></a> } @empty { <p class="my-4">Todavía no hay cuentas.</p> }<a routerLink="/app/accounts" class="inline-block mt-4 text-brand-700 underline">Gestionar cuentas</a></article>
      <article class="finance-card"><h2 class="text-xl font-bold">Gastos por categoría</h2>@for (item of data.distribution; track item.name) { <div class="mt-4"><div class="flex justify-between gap-3"><span>{{ item.name }}</span><strong>{{ money(item.amount) }}</strong></div><progress class="mt-2 w-full accent-teal-700" [value]="+item.amount" [max]="+data.expense" [attr.aria-label]="item.name"></progress></div> } @empty { <p class="my-4">Sin gastos registrados en este mes.</p> }</article></section>
      <section class="finance-card mt-6 mb-20"><h2 class="text-xl font-bold">Últimos movimientos del mes</h2>@for (operation of data.recent; track operation.id) { <div class="flex flex-wrap justify-between gap-3 border-b py-4"><div><p class="font-semibold">{{ operation.description || operation.category_name || operation.type }}</p><p class="text-sm text-slate-500">{{ operation.effective_date }} · {{ operation.account_name }}{{ operation.destination_name ? ' → ' + operation.destination_name : '' }}</p></div><strong>{{ operation.type === 'expense' ? '−' : operation.type === 'income' ? '+' : '' }}{{ money(operation.amount) }}</strong></div> } @empty { <p class="my-4">Este mes todavía no tiene movimientos. Registrá el primero para ver tus finanzas aquí.</p> }<a routerLink="/app/transactions" class="inline-block mt-4 text-brand-700 underline">Ver movimientos</a></section>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardPageComponent {
  readonly auth = inject(AuthService); private readonly finance = inject(FinanceService); readonly summary = signal<Summary | null>(null); readonly loading = signal(false); readonly error = signal(''); readonly money = money;
  month = localDate().slice(0, 7); private version = 0;
  constructor() { effect(() => { const household = this.auth.activeHousehold()?.id; this.finance.changed(); this.summary.set(null); this.error.set(''); if (household) void this.load(); }); }
  kpis(data: Summary): { label: string; value: string }[] { return [{ label: 'Saldo consolidado actual', value: data.balance }, { label: 'Ingresos del mes', value: data.income }, { label: 'Gastos del mes', value: data.expense }, { label: 'Resultado neto del mes', value: data.net }]; }
  async load(): Promise<void> { const version = ++this.version; this.loading.set(true); this.error.set(''); try { const data = await this.finance.read<Summary>('dashboard/summary/', { month: this.month }); if (version === this.version) this.summary.set(data); } catch (error) { if (version === this.version) this.error.set(financeError(error)); } finally { if (version === this.version) this.loading.set(false); } }
}
