import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { FinanceService, FinancialAccount, Summary, cents, financeError, localDate, money } from '../../core/finance.service';

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
        <article class="finance-card" data-testid="monthly-income">
          <h2 class="text-sm font-semibold text-slate-500">Ingresos totales del mes</h2>
          <p class="kpi-amount text-brand-700 dark:text-teal-300">{{ monthlyIncome(data) }}</p>
          @if (hasOpeningIncome(data)) { <p class="mt-2 text-xs text-slate-500">Incluye los saldos iniciales registrados este mes.</p> }
          <dl class="mt-4 text-sm">
            @for (account of data.accounts; track account.id) {
              <div class="flex justify-between gap-3 py-2" data-testid="account-income"><dt class="min-w-0 break-words">{{ account.name }}</dt><dd class="shrink-0 font-semibold">{{ accountIncome(account) }}</dd></div>
            } @empty { <p class="text-slate-500">Todavía no hay cuentas.</p> }
          </dl>
        </article>
        <article class="finance-card" data-testid="monthly-expense">
          <h2 class="text-sm font-semibold text-slate-500">Gastos totales del mes</h2>
          <p class="kpi-amount">{{ money(data.expense, data.currency) }}</p>
        </article>
        <article class="available-card" data-testid="available-balance">
          <h2 class="text-base font-semibold text-teal-100">Disponible</h2>
          @for (balance of data.available_balances; track balance.currency) {
            <p class="kpi-amount available-amount">{{ money(balance.amount, balance.currency) }}</p>
          }
          <p class="mt-4 text-sm text-teal-100">Saldo actual de tus cuentas activas</p>
        </article>
      </section>
      <section class="finance-card mt-6 mb-20" aria-label="Resumen de compras en cuotas">
        <h2 class="text-xl font-bold">Compras en cuotas</h2>
        @for (purchase of data.installment_purchases ?? []; track purchase.id) {
          <article class="border-b border-slate-200 py-5 dark:border-slate-800" data-testid="installment-purchase">
            <div class="flex flex-wrap items-center justify-between gap-2"><h3 class="font-semibold break-words min-w-0">{{ purchase.description }}</h3><span class="text-sm text-slate-500">{{ purchase.card_name || purchase.creditor || 'Sin tarjeta' }}</span></div>
            <p class="mt-2 text-sm">{{ purchase.paid_installments }} de {{ purchase.installments_count }} cuotas pagadas · {{ purchase.remaining_installments }} pendientes</p>
            <dl class="account-totals">
              <div><dt>Total de la compra</dt><dd>{{ money(purchase.amount, data.currency) }}</dd></div>
              <div><dt>Total pagado</dt><dd>{{ money(purchase.paid_amount, data.currency) }}</dd></div>
              <div><dt>Total pendiente</dt><dd>{{ money(purchase.pending_amount, data.currency) }}</dd></div>
            </dl>
          </article>
        } @empty { <p class="mt-4 text-sm text-slate-500">No tenés compras en cuotas.</p> }
      </section>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardPageComponent {
  readonly auth = inject(AuthService); private readonly finance = inject(FinanceService); readonly summary = signal<Summary | null>(null); readonly loading = signal(false); readonly error = signal(''); readonly money = money;
  month = localDate().slice(0, 7); private version = 0;
  constructor() { effect(() => { const household = this.auth.activeHousehold()?.id; this.finance.changed(); ++this.version; this.summary.set(null); this.error.set(''); if (household) void this.load(); }); }
  monthlyIncome(data: Summary): string {
    return money(this.sumAmounts([data.income, ...data.accounts.map(account => account.monthly_opening ?? '0')]), data.currency);
  }
  accountIncome(account: FinancialAccount): string {
    return money(this.sumAmounts([account.monthly_income ?? '0', account.monthly_opening ?? '0']), account.currency);
  }
  hasOpeningIncome(data: Summary): boolean { return data.accounts.some(account => cents(account.monthly_opening ?? '0') !== 0n); }
  private sumAmounts(amounts: string[]): string {
    const total = amounts.reduce((sum, amount) => sum + cents(amount), 0n);
    const absolute = total < 0n ? -total : total;
    return `${total < 0n ? '-' : ''}${absolute / 100n}.${String(absolute % 100n).padStart(2, '0')}`;
  }
  changePeriod(value: string): void { this.month = value; void this.load(); }
  async load(): Promise<void> { const version = ++this.version; this.loading.set(true); this.error.set(''); this.summary.set(null); try { const data = await this.finance.read<Summary>('dashboard/summary/', { month: this.month }); if (version === this.version) this.summary.set(data); } catch (error) { if (version === this.version) this.error.set(financeError(error)); } finally { if (version === this.version) this.loading.set(false); } }
}
