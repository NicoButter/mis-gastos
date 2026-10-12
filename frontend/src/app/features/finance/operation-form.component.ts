import { ChangeDetectionStrategy, Component, effect, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { Category, FinanceService, FinancialAccount, Operation, financeError, localDate } from '../../core/finance.service';

@Component({
  selector: 'gst-operation-form', imports: [FormsModule, RouterLink],
  template: `
    @if (error()) { <p class="notice-error" role="alert">{{ error() }}</p> }
    @if (success()) { <p class="notice-success" role="status">{{ success() }}</p> }
    @if (loading()) { <p role="status">Cargando opciones…</p> }
    @if (!loading() && accounts().length === 0) { <p class="notice-success">Necesitás una cuenta activa. <a routerLink="/app/accounts" class="underline">Crear cuenta</a></p> }
    <fieldset [disabled]="busy()" [attr.aria-busy]="busy()"><form #form="ngForm" (ngSubmit)="save()" class="grid gap-5" [class.mt-5]="!quick()" [class.quick-form]="quick()">
      @if (!quick() && !operation()) { <label>Operación<select class="form-input" name="type" [(ngModel)]="draft.type" (ngModelChange)="draft.category_id = ''; draft.destination_id = ''"><option value="expense">Gasto</option><option value="income">Ingreso</option><option value="transfer">Transferencia</option></select></label> }
      <label [class.quick-amount]="quick()">Importe · ARS<input class="form-input amount-input" name="amount" [(ngModel)]="draft.amount" inputmode="decimal" placeholder="0,00" pattern="[0-9]+([.,][0-9]{1,2})?" required [attr.aria-describedby]="quick() ? null : 'amount-help'"></label>
      @if (!quick()) { <p id="amount-help" class="text-sm text-slate-500 -mt-3">Mayor que cero, hasta dos decimales.</p> }
      @if (draft.type !== 'transfer') {
        @if (quick()) {
          <label>Categoría<select class="form-input" name="category" aria-label="Categoría" [(ngModel)]="draft.category_id" required><option value="" disabled>Elegí una categoría</option>@for (category of filteredCategories(); track category.id) { <option [value]="category.id">{{ category.name }}</option> }</select></label>
          @if (!loading() && filteredCategories().length === 0) { <p class="text-sm text-slate-500 -mt-3">Necesitás una categoría de gasto. <a routerLink="/app/categories" class="font-semibold text-brand-700 underline dark:text-teal-300">Crear categoría</a></p> }
        } @else {
          <fieldset><legend class="mb-2">Categoría</legend><div class="flex flex-wrap gap-2">@for (category of filteredCategories(); track category.id) { <button type="button" class="min-h-11 rounded-full border px-4 py-2" [class.bg-brand-700]="draft.category_id === category.id" [class.text-white]="draft.category_id === category.id" [attr.aria-pressed]="draft.category_id === category.id" (click)="draft.category_id = category.id">{{ category.name }}</button> }</div></fieldset>
        }
      }
      <label>{{ draft.type === 'income' ? 'Cuenta de destino' : 'Cuenta de origen' }}<select class="form-input" name="account" [(ngModel)]="draft.account_id" required><option value="">Elegí una cuenta</option>@for (account of accounts(); track account.id) { <option [value]="account.id">{{ account.name }}</option> }</select></label>
      @if (draft.type === 'transfer') { <label>Cuenta de destino<select class="form-input" name="destination" [(ngModel)]="draft.destination_id" required><option value="">Elegí el destino</option>@for (account of accounts(); track account.id) { @if (account.id !== draft.account_id) { <option [value]="account.id">{{ account.name }}</option> } }</select></label> }
      @if (quick()) {
        <details class="quick-details rounded-xl border border-slate-200 dark:border-slate-700">
          <summary class="flex min-h-11 cursor-pointer items-center justify-between gap-3 px-3 py-3 text-sm"><span class="font-medium">Fecha y nota</span><span class="text-slate-500 dark:text-slate-400">{{ draft.effective_date === today() ? 'Hoy' : displayDate(draft.effective_date) }} <span aria-hidden="true" class="details-chevron ml-1 inline-block">⌄</span></span></summary>
          <div class="grid gap-4 px-3 pb-4">
            <label>Fecha<input class="form-input" type="date" name="date" [(ngModel)]="draft.effective_date" required></label>
            <label>Descripción opcional<input class="form-input" name="description" [(ngModel)]="draft.description" maxlength="500" placeholder="¿En qué gastaste?"></label>
          </div>
        </details>
      } @else {
        <label>Fecha<input class="form-input" type="date" name="date" [(ngModel)]="draft.effective_date" required></label>
        <label>Descripción opcional<input class="form-input" name="description" [(ngModel)]="draft.description" maxlength="500"></label>
      }
      <button class="btn-primary w-full min-h-12" [disabled]="form.invalid || !valid() || busy() || loading()">{{ busy() ? 'Guardando…' : operation() ? 'Guardar corrección' : draft.type === 'expense' ? 'Guardar gasto' : draft.type === 'income' ? 'Guardar ingreso' : 'Guardar transferencia' }}</button>
    </form></fieldset>
  `,
  styles: `
    .quick-form > label, .quick-details label { font-size: .875rem; font-weight: 600; }
    .quick-form .form-input { font-weight: 400; }
    .quick-amount { padding: 1.25rem; border-radius: 1rem; background: light-dark(#f0fdfa, #132e30); color: light-dark(#115e59, #99f6e4); }
    .quick-amount .amount-input { margin-top: .5rem; padding: .25rem 0; border: 0; border-radius: .25rem; background: transparent; font-size: clamp(2.25rem, 8vw, 3rem); font-weight: 700; line-height: 1.25; font-variant-numeric: tabular-nums; }
    .quick-amount .amount-input::placeholder { color: light-dark(#5f9991, #608d8a); opacity: 1; }
    .quick-details summary::-webkit-details-marker { display: none; }
    .quick-details[open] .details-chevron { transform: rotate(180deg); }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OperationFormComponent {
  readonly quick = input(false); readonly operation = input<Operation | null>(null); readonly saved = output<Operation>();
  private readonly finance = inject(FinanceService); private readonly auth = inject(AuthService);
  readonly accounts = signal<FinancialAccount[]>([]); readonly categories = signal<Category[]>([]); readonly busy = signal(false); readonly loading = signal(false); readonly error = signal(''); readonly success = signal('');
  draft = { type: 'expense', amount: '', account_id: '', destination_id: '', category_id: '', effective_date: localDate(), description: '' };
  private retry = { fingerprint: '', key: '' };
  readonly today = localDate;
  displayDate(value: string): string { return value.split('-').reverse().join('/'); }
  constructor() { effect(() => { const household = this.auth.activeHousehold()?.id; const operation = this.operation(); this.reset(operation); this.accounts.set([]); this.categories.set([]); if (household) void this.load(household); }); }
  private reset(operation: Operation | null): void { this.draft = operation ? { type: operation.type, amount: operation.amount, account_id: operation.account_id, destination_id: operation.destination_id ?? '', category_id: operation.category_id ?? '', effective_date: operation.effective_date, description: operation.description } : { type: 'expense', amount: '', account_id: '', destination_id: '', category_id: '', effective_date: localDate(), description: '' }; this.error.set(''); this.success.set(''); this.retry = { fingerprint: '', key: '' }; }
  async load(household: string): Promise<void> { this.loading.set(true); try { const [accounts, categories] = await Promise.all([this.finance.all<FinancialAccount>('accounts'), this.finance.all<Category>('categories')]); if (household !== this.auth.activeHousehold()?.id) return; const frequent = (a: {usage_count?: number}, b: {usage_count?: number}) => (b.usage_count ?? 0) - (a.usage_count ?? 0); this.accounts.set(accounts.filter(a => a.is_active).sort(frequent)); this.categories.set(categories.filter(c => c.is_active).sort(frequent)); if (!this.draft.account_id && (this.quick() || this.accounts().length === 1)) this.draft.account_id = this.accounts()[0]?.id ?? ''; } catch (error) { if (household === this.auth.activeHousehold()?.id) this.error.set(financeError(error)); } finally { if (household === this.auth.activeHousehold()?.id) this.loading.set(false); } }
  filteredCategories(): Category[] { return this.categories().filter(c => c.type === this.draft.type); }
  valid(): boolean { return /^\d+([.,]\d{1,2})?$/.test(this.draft.amount) && Number(this.draft.amount.replace(',', '.')) > 0 && this.accounts().some(a => a.id === this.draft.account_id) && (this.draft.type === 'transfer' ? this.accounts().some(a => a.id === this.draft.destination_id) && this.draft.destination_id !== this.draft.account_id : this.filteredCategories().some(c => c.id === this.draft.category_id)); }
  async save(): Promise<void> {
    if (this.busy() || this.loading() || !this.draft.effective_date || !this.valid()) return;
    const household = this.auth.activeHousehold()?.id;
    const operation = this.operation();
    const payload = { ...this.draft, amount: this.draft.amount.replace(',', '.'), category_id: this.draft.type === 'transfer' ? null : this.draft.category_id, destination_id: this.draft.type === 'transfer' ? this.draft.destination_id : null, ...(operation ? { expected_revision: operation.revision } : {}) };
    const path = operation ? `transactions/${operation.id}/` : this.draft.type === 'transfer' ? 'transfers/' : 'transactions/';
    const fingerprint = JSON.stringify({ payload, path, household: this.auth.activeHousehold()?.id });
    if (fingerprint !== this.retry.fingerprint) this.retry = { fingerprint, key: crypto.randomUUID() };
    this.busy.set(true); this.error.set(''); this.success.set('');
    try { const result = await this.finance.write<Operation>(path, payload, this.retry.key, !!operation); if (household !== this.auth.activeHousehold()?.id) return; this.saved.emit(result); if (!operation) { const account = this.draft.account_id, category = this.draft.category_id; this.reset(null); this.draft.account_id = account; this.draft.category_id = category; } this.success.set('Movimiento guardado. Podés registrar otro.'); } catch (error) { if (household === this.auth.activeHousehold()?.id) this.error.set(financeError(error)); } finally { this.busy.set(false); }
  }
}
