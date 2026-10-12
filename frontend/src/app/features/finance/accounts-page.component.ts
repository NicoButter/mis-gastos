import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { FinanceService, FinancialAccount, financeError, localDate, money, cents } from '../../core/finance.service';

import { PeriodSelectorComponent } from '../../shared/period-selector.component';

@Component({
  imports: [FormsModule, RouterLink, PeriodSelectorComponent],
  template: `
    <header class="flex flex-wrap items-center justify-between gap-4"><div><p class="text-sm text-brand-700">{{ auth.activeHousehold()?.name }}</p><h1 class="text-3xl font-black">Cuentas</h1><p class="mt-2 text-slate-500">Saldos calculados desde tus movimientos · ARS</p></div>@if (canManage()) { <button class="btn-primary" (click)="edit()">Agregar cuenta</button> }</header>
    <section class="mt-6 grid gap-4 sm:grid-cols-2"><gst-period-selector [month]="month" (monthChange)="changePeriod($event)" /><label class="text-sm font-semibold">Consultar cuenta<select class="form-input" [(ngModel)]="selectedAccountId"><option value="">Todas las cuentas</option>@for (account of accounts(); track account.id) { <option [value]="account.id">{{ account.name }}</option> }</select></label></section>
    <p class="mt-3 text-sm text-slate-500">Resumen de {{ month }} · los saldos son actuales. Las entradas incluyen ingresos, transferencias recibidas y aperturas; las salidas incluyen gastos, transferencias enviadas y pagos de cuotas.</p>
    @if (error()) { <p class="notice-error" role="alert">{{ error() }}</p> }
    @if (success()) { <p class="notice-success" role="status">{{ success() }}</p> }
    @if (loading()) { <p role="status" class="mt-6">Cargando cuentas…</p> }
    <section class="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      @for (account of visibleAccounts(); track account.id) {
        <article class="finance-card"><div class="flex justify-between gap-2"><h2 class="text-lg font-bold break-words">{{ account.name }}</h2><span class="text-sm">{{ account.is_active ? 'Activa' : 'Archivada' }}</span></div><p class="text-sm text-slate-500">{{ kindLabel(account.kind) }}</p><p class="mt-4 text-sm text-slate-500">Saldo actual</p><p class="mt-1 text-3xl font-black" [class.text-red-600]="account.balance.startsWith('-')">{{ money(account.balance, account.currency) }} <span class="text-sm">{{ account.currency }}</span></p>
          <dl class="account-totals"><div><dt>Entradas del mes</dt><dd>{{ money(account.monthly_inflow ?? '0') }}</dd></div><div><dt>Salidas del mes</dt><dd>{{ money(account.monthly_outflow ?? '0') }}</dd></div><div><dt>Ingresos del mes</dt><dd class="text-brand-700 dark:text-teal-300">{{ money(account.monthly_income ?? '0') }}</dd></div><div><dt>Gastos del mes</dt><dd>{{ money(account.monthly_expense ?? '0') }}</dd></div></dl>
          <p class="mt-3 text-sm">Resultado del mes: <strong>{{ monthlyNet(account) }}</strong></p>
          <details class="mt-3 text-sm"><summary class="cursor-pointer">Detalle de entradas y salidas</summary><dl class="account-totals"><div><dt>Saldo inicial registrado</dt><dd>{{ money(account.monthly_opening ?? '0') }}</dd></div><div><dt>Pagos de cuotas</dt><dd>{{ money(account.monthly_card_payments ?? '0') }}</dd></div><div><dt>Transferencias recibidas</dt><dd>{{ money(account.monthly_transfer_in ?? '0') }}</dd></div><div><dt>Transferencias enviadas</dt><dd>{{ money(account.monthly_transfer_out ?? '0') }}</dd></div></dl><p class="mt-3 text-slate-500">Las transferencias y aperturas no son ingresos ni gastos. El pago de una cuota financiada es una salida: sus cuotas se contabilizan en el resumen del hogar, por vencimiento.</p></details><p class="break-words">{{ account.description }}</p><div class="mt-4 flex flex-wrap gap-3"><a class="text-brand-700 underline" routerLink="/app/transactions" [queryParams]="{account: account.id}">Movimientos</a>@if (canManage()) { <button (click)="edit(account)" class="text-brand-700 underline">Editar</button><button [disabled]="busy()" (click)="archive(account)" class="underline">{{ account.is_active ? 'Archivar' : 'Reactivar' }}</button> }</div></article>
      } @empty { @if (!loading()) { <div class="finance-card"><h2 class="font-bold">Todavía no hay cuentas</h2><p>Creá tu cuenta de efectivo, banco o billetera para empezar.</p></div> } }
    </section>
    @if (showForm()) {
      <section class="finance-card mt-8 max-w-xl"><h2 class="text-xl font-bold">{{ editingId ? 'Editar cuenta' : 'Nueva cuenta' }}</h2><form #form="ngForm" (ngSubmit)="save()" class="mt-4 grid gap-4">
        <label>Nombre<input class="form-input" name="name" [(ngModel)]="draft.name" required maxlength="120"></label>
        <label>Tipo<select class="form-input" name="kind" [(ngModel)]="draft.kind" required><option value="cash">Efectivo</option><option value="bank">Banco</option><option value="wallet">Billetera virtual</option><option value="other">Otra cuenta</option></select></label>
        <p>Moneda: ARS</p>
        @if (!editingId) { <label>Saldo inicial<input class="form-input" name="opening" [(ngModel)]="draft.opening_balance" inputmode="decimal" pattern="[0-9]+([.,][0-9]{1,2})?" required></label><label>Fecha de apertura<input class="form-input" type="date" name="date" [(ngModel)]="draft.opening_date" required></label> }
        <label>Descripción<input class="form-input" name="description" [(ngModel)]="draft.description" maxlength="500"></label>
        <div class="flex gap-3"><button class="btn-primary" [disabled]="form.invalid || busy()">{{ busy() ? 'Guardando…' : 'Guardar cuenta' }}</button><button type="button" [disabled]="busy()" (click)="showForm.set(false)">Cancelar</button></div>
      </form></section>
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AccountsPageComponent {
  readonly auth = inject(AuthService);
  readonly finance = inject(FinanceService);
  readonly accounts = signal<FinancialAccount[]>([]);
  readonly loading = signal(false); readonly busy = signal(false); readonly error = signal(''); readonly success = signal(''); readonly showForm = signal(false);
  readonly money = money;
  month = localDate().slice(0, 7); selectedAccountId = ''; private loadVersion = 0;
  editingId = ''; private retry = { fingerprint: '', key: '' };
  draft = { name: '', kind: 'cash', description: '', opening_balance: '0', opening_date: localDate() };
  constructor() {
    effect(() => { this.auth.activeHousehold(); ++this.loadVersion; this.accounts.set([]); this.selectedAccountId = ''; this.showForm.set(false); this.error.set(''); this.success.set(''); });
    effect(() => { const household = this.auth.activeHousehold()?.id; this.finance.changed(); if (household) void this.load(household); });
  }
  visibleAccounts(): FinancialAccount[] { return this.accounts().filter(account => !this.selectedAccountId || account.id === this.selectedAccountId); }
  monthlyNet(account: FinancialAccount): string {
    const value = cents(account.monthly_income ?? '0') - cents(account.monthly_expense ?? '0');
    const absolute = value < 0n ? -value : value;
    return money(`${value < 0n ? '-' : ''}${absolute / 100n}.${String(absolute % 100n).padStart(2, '0')}`, account.currency);
  }
  changePeriod(value: string): void { this.month = value; void this.load(); }
  async load(household = this.auth.activeHousehold()?.id): Promise<void> {
    const version = ++this.loadVersion;
    this.loading.set(true); this.accounts.set([]); this.error.set('');
    try {
      const data = await this.finance.all<FinancialAccount>('accounts', { month: this.month });
      if (version === this.loadVersion && household === this.auth.activeHousehold()?.id) this.accounts.set(data);
    } catch (error) { if (version === this.loadVersion && household === this.auth.activeHousehold()?.id) this.error.set(financeError(error)); }
    finally { if (version === this.loadVersion) this.loading.set(false); }
  }
  edit(account?: FinancialAccount): void { this.editingId = account?.id ?? ''; this.draft = { name: account?.name ?? '', kind: account?.kind ?? 'cash', description: account?.description ?? '', opening_balance: '0', opening_date: localDate() }; this.showForm.set(true); this.error.set(''); this.success.set(''); this.retry = { fingerprint: '', key: '' }; }
  kindLabel(kind: string): string { return ({ cash: 'Efectivo', bank: 'Banco', wallet: 'Billetera virtual', other: 'Otra cuenta' } as Record<string, string>)[kind] ?? kind; }
  canManage(): boolean { return ['owner', 'admin'].includes(this.auth.activeHousehold()?.role ?? ''); }
  async save(): Promise<void> {
    if (this.busy()) return;
    const household = this.auth.activeHousehold()?.id;
    const payload = this.editingId ? { name: this.draft.name, kind: this.draft.kind, description: this.draft.description } : { ...this.draft, opening_balance: this.draft.opening_balance.replace(',', '.') };
    const path = this.editingId ? `accounts/${this.editingId}/` : 'accounts/';
    const fingerprint = JSON.stringify({ path, payload, household: this.auth.activeHousehold()?.id });
    if (this.retry.fingerprint !== fingerprint) this.retry = { fingerprint, key: crypto.randomUUID() };
    this.busy.set(true); this.error.set('');
    try { await this.finance.write(path, payload, this.retry.key, !!this.editingId); if (household !== this.auth.activeHousehold()?.id) return; this.showForm.set(false); this.success.set('Cuenta guardada.'); await this.load(); } catch (error) { if (household === this.auth.activeHousehold()?.id) this.error.set(financeError(error)); } finally { this.busy.set(false); }
  }
  async archive(account: FinancialAccount): Promise<void> { if (this.busy() || !confirm(`${account.is_active ? 'Archivar' : 'Reactivar'} ${account.name}? El historial se conserva.`)) return; this.busy.set(true); try { await this.finance.write(`accounts/${account.id}/`, { is_active: !account.is_active }, crypto.randomUUID(), true); await this.load(); } catch (error) { this.error.set(financeError(error)); } finally { this.busy.set(false); } }
}
