import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { FinanceService, Summary, financeError, localDate, money, spendingRatio } from '../../core/finance.service';

import { PeriodSelectorComponent } from '../../shared/period-selector.component';

@Component({
  imports: [PeriodSelectorComponent, RouterLink],
  template: `
    <header class="flex flex-wrap justify-between gap-4"><div><p class="text-sm font-semibold text-brand-700">{{ auth.activeHousehold()?.name || 'Seleccioná un hogar' }}</p><h1 class="text-3xl font-black mt-1">Panel financiero</h1></div><a routerLink="/app/quick" class="btn-primary">+ Gasto rápido</a></header>
    <div class="mt-6"><gst-period-selector [month]="month" (monthChange)="changePeriod($event)" /></div>
    @if (error()) { <p class="notice-error" role="alert">{{ error() }}</p><button class="underline" (click)="load()">Reintentar</button> }
    @if (loading()) { <p class="mt-6" role="status">Cargando resumen…</p> }
    @if (summary(); as data) {
      <section class="dashboard-kpis mt-6" aria-label="Resumen financiero">
        <article class="available-card" data-testid="available-balance"><p class="text-base font-semibold text-teal-100">Saldo disponible</p>@for (balance of data.available_balances; track balance.currency) { <p class="kpi-amount available-amount">{{ money(balance.amount, balance.currency) }} <span class="text-sm font-medium">{{ balance.currency }}</span></p> }<p class="mt-4 text-sm text-teal-100">Saldo actual · efectivo, bancos y billeteras activas</p><a routerLink="/app/accounts" class="inline-flex mt-3 underline text-sm">Ver mis cuentas →</a></article>
        <article class="finance-card" data-testid="monthly-income"><h2 class="text-sm font-semibold text-slate-500">Ingresos del mes</h2><p class="kpi-amount text-brand-700 dark:text-teal-300">{{ money(data.income, data.currency) }}</p><p class="mt-3 text-sm text-slate-500">{{ data.month }} · sin aperturas ni transferencias</p></article>
        <article class="finance-card" data-testid="monthly-expense"><h2 class="text-sm font-semibold text-slate-500">Gastos del mes</h2><p class="kpi-amount">{{ money(data.expense, data.currency) }}</p><p class="mt-3 text-sm text-slate-500">{{ data.month }} · incluye cuotas de tarjeta, sin duplicar pagos</p></article>
      </section>
      <section class="finance-card mt-4" aria-label="Resultado del período">
        <div class="flex flex-wrap justify-between gap-3 items-center"><div><h2 class="font-semibold">Resultado del mes</h2><p class="text-sm text-slate-500">Ingresos menos gastos de {{ data.month }}</p></div><p class="text-2xl font-bold" data-testid="monthly-net" [class.text-red-600]="data.net.startsWith('-')">{{ money(data.net, data.currency) }}</p></div>
        @if (ratio(data); as usage) {
          <div class="mt-5 flex flex-wrap justify-between gap-2 text-sm"><p>{{ usage.percent }} de los ingresos destinado a gastos</p><strong [class.text-red-600]="usage.overspent">{{ usage.overspent ? 'Sobregasto: los gastos superan los ingresos' : 'Gastos dentro de los ingresos' }}</strong></div>
          <div class="spending-track mt-2" role="progressbar" aria-label="Gastos frente a ingresos" aria-valuemin="0" aria-valuemax="100" [attr.aria-valuenow]="usage.width" [attr.aria-valuetext]="usage.percent + (usage.overspent ? ' · sobregasto' : '')"><div class="spending-fill" [class.overspent]="usage.overspent" [style.width.%]="usage.width"></div></div>
        } @else { <p class="mt-4 text-sm text-slate-500">Sin ingresos positivos en este período para comparar los gastos.</p> }
      </section>
      <p class="mt-3 text-sm text-slate-500">{{ data.count }} movimientos del mes. El saldo disponible es actual y no cambia al consultar otro período.</p>
      <section class="mt-6 grid gap-6 xl:grid-cols-2"><article class="finance-card"><h2 class="text-xl font-bold">Cuentas y saldos</h2>@for (account of data.accounts; track account.id) { <a routerLink="/app/transactions" [queryParams]="{account: account.id}" class="account-balance-row flex flex-wrap justify-between gap-2 border-b py-4"><span>{{ account.name }}{{ account.is_active ? '' : ' · Archivada' }}</span><strong>{{ money(account.balance) }}</strong></a> } @empty { <p class="my-4">Todavía no hay cuentas.</p> }<a routerLink="/app/accounts" class="inline-block mt-4 text-brand-700 underline">Gestionar cuentas</a></article>
      <article class="finance-card"><h2 class="text-xl font-bold">Gastos por categoría</h2>@for (item of data.distribution; track $index) { <div class="mt-4"><div class="flex justify-between gap-3"><span>{{ item.name }}</span><strong>{{ money(item.amount) }}</strong></div><progress class="mt-2 w-full accent-teal-700" [value]="+item.amount" [max]="+data.expense" [attr.aria-label]="item.name"></progress></div> } @empty { <p class="my-4">Sin gastos registrados en este mes.</p> }</article></section>
      <section class="finance-card mt-6"><h2 class="text-xl font-bold">Próximas cuotas y vencimientos</h2><p class="mt-2">Pendiente total: {{ money(data.card_pending ?? '0') }}</p>@for (installment of data.upcoming_installments ?? []; track installment.id) { <div class="flex flex-wrap justify-between gap-3 border-b py-3"><span>{{ installment.card_name }} · {{ installment.description }} · Cuota {{ installment.number }}/{{ installment.installments_count }}<br>Vence {{ installment.due_date }}</span><strong>{{ money(installment.amount) }}</strong></div> } @empty { <p class="mt-3">Sin cuotas pendientes.</p> }<a routerLink="/app/cards" class="inline-block mt-4 underline text-brand-700">Administrar tarjetas y pagos</a></section>
      <section class="finance-card mt-6 mb-20"><h2 class="text-xl font-bold">Últimos movimientos del mes</h2>@for (operation of data.recent; track operation.id) { <div class="flex flex-wrap justify-between gap-3 border-b py-4"><div><p class="font-semibold">{{ operation.description || operation.category_name || operation.type }}</p><p class="text-sm text-slate-500">{{ operation.effective_date }} · {{ operation.account_name }}{{ operation.destination_name ? ' → ' + operation.destination_name : '' }}</p></div><strong>{{ (operation.type === 'expense' || operation.type === 'card_payment') ? '−' : operation.type === 'income' ? '+' : '' }}{{ money(operation.amount) }}</strong></div> } @empty { <p class="my-4">Este mes todavía no tiene movimientos. Registrá el primero para ver tus finanzas aquí.</p> }<a routerLink="/app/transactions" class="inline-block mt-4 text-brand-700 underline">Ver movimientos</a></section>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardPageComponent {
  readonly auth = inject(AuthService); private readonly finance = inject(FinanceService); readonly summary = signal<Summary | null>(null); readonly loading = signal(false); readonly error = signal(''); readonly money = money;
  month = localDate().slice(0, 7); private version = 0;
  constructor() { effect(() => { const household = this.auth.activeHousehold()?.id; this.finance.changed(); ++this.version; this.summary.set(null); this.error.set(''); if (household) void this.load(); }); }
  ratio(data: Summary) { return spendingRatio(data.income, data.expense); }
  changePeriod(value: string): void { this.month = value; void this.load(); }
  async load(): Promise<void> { const version = ++this.version; this.loading.set(true); this.error.set(''); this.summary.set(null); try { const data = await this.finance.read<Summary>('dashboard/summary/', { month: this.month }); if (version === this.version) this.summary.set(data); } catch (error) { if (version === this.version) this.error.set(financeError(error)); } finally { if (version === this.version) this.loading.set(false); } }
}
