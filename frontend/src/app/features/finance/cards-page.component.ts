import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/auth.service';
import { CardInstallment, CardPurchase, Category, CreditCard, FinanceService, FinancialAccount, financeError, localDate, money, cents } from '../../core/finance.service';

@Component({
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <header><h1 class="text-3xl font-black">{{ installmentsOnly ? 'Compras en cuotas' : 'Tarjetas de crédito' }}</h1><p class="mt-2 text-slate-500">Compras y cuotas en ARS. Los pagos descuentan saldo de una cuenta, sin duplicar gastos.</p></header>
    @if (error()) { <p class="notice-error" role="alert">{{ error() }}</p><button class="underline" (click)="load()">Reintentar carga</button> }
    @if (success()) { <p class="notice-success" role="status">{{ success() }}</p> }
    @if (loading()) { <p role="status">Cargando tarjetas…</p> }
    @if (installmentsOnly) { <button class="btn-primary mt-4" [disabled]="busy()" (click)="buy()">Nueva compra en cuotas</button> }
    @if (!installmentsOnly && canManage()) { <button class="btn-primary mt-4" [disabled]="busy()" (click)="edit()">Agregar tarjeta</button> }
    @if (!installmentsOnly) { <section class="grid gap-4 mt-6 md:grid-cols-2 xl:grid-cols-3">
      @for (card of cards(); track card.id) {
        <article class="finance-card"><h2 class="text-xl font-bold break-words">{{ card.name }}</h2><p>{{ card.bank }} · {{ card.is_active ? 'Activa' : 'Archivada' }}</p><p>Cierre: día {{ card.closing_day }} · Vencimiento: día {{ card.due_day }}</p><div class="flex flex-wrap gap-3 mt-4">@if (canManage()) { <button class="underline" [disabled]="busy()" (click)="edit(card)">Editar</button><button class="underline" [disabled]="busy()" (click)="archive(card)">{{ card.is_active ? 'Archivar' : 'Reactivar' }}</button> } @if (card.is_active) { <button class="underline" [disabled]="busy()" (click)="buy(card)">Registrar compra</button> }</div></article>
      } @empty { <p>Todavía no hay tarjetas.</p> }
    </section> }
    @if (formMode === 'card') {
      <section class="finance-card mt-6 max-w-xl"><h2 class="text-xl font-bold">{{ editingId ? 'Editar tarjeta' : 'Nueva tarjeta' }}</h2><form #form="ngForm" (ngSubmit)="saveCard()" class="grid gap-4 mt-4"><fieldset [disabled]="busy()" class="grid gap-4">
        <label>Banco<input class="form-input" name="bank" [(ngModel)]="cardDraft.bank" required maxlength="120"></label><label>Nombre<input class="form-input" name="name" [(ngModel)]="cardDraft.name" required maxlength="120"></label>
        <label>Día de cierre<input class="form-input" type="number" name="closing" [(ngModel)]="cardDraft.closing_day" min="1" max="31" required></label><label>Día de vencimiento<input class="form-input" type="number" name="due" [(ngModel)]="cardDraft.due_day" min="1" max="31" required></label><p class="text-sm">Los días inexistentes se ajustan al último día del mes. Editar no cambia las cuotas ya registradas.</p><div class="flex gap-3"><button class="btn-primary" [disabled]="form.invalid">Guardar tarjeta</button><button type="button" (click)="formMode = ''">Cancelar</button></div>
      </fieldset></form></section>
    }
    @if (formMode === 'purchase') {
      <section class="finance-card mt-6 max-w-xl"><h2 class="text-xl font-bold">Registrar compra</h2><form #form="ngForm" (ngSubmit)="savePurchase()" class="mt-4"><fieldset [disabled]="busy()" class="grid gap-4">
        @if (!installmentsOnly) { <label>Tarjeta<select class="form-input" name="card" [(ngModel)]="purchaseDraft.card_id" required>@for (card of cards(); track card.id) { @if (card.is_active) { <option [value]="card.id">{{ card.name }}</option> } }</select></label> }
        @if (installmentsOnly) { <label>Vendedor o acreedor<input class="form-input" name="creditor" [(ngModel)]="purchaseDraft.creditor" maxlength="200"></label><label>Fecha de la primera cuota<input class="form-input" type="date" name="firstDue" [(ngModel)]="purchaseDraft.first_due_date" required></label><p>Frecuencia mensual · no se descuenta saldo al crear la compra.</p> }
        <label>Descripción<input class="form-input" name="description" [(ngModel)]="purchaseDraft.description" required maxlength="500"></label><label>Importe total<input class="form-input" name="amount" [(ngModel)]="purchaseDraft.amount" required inputmode="decimal" pattern="[0-9]+([.,][0-9]{1,2})?"></label>@if (!installmentsOnly) { <label>Fecha de compra<input class="form-input" type="date" name="date" [(ngModel)]="purchaseDraft.purchase_date" required></label> }<label>Cantidad de cuotas<input class="form-input" type="number" name="count" [(ngModel)]="purchaseDraft.installments_count" min="1" max="120" required></label><label>Categoría<select class="form-input" name="category" [(ngModel)]="purchaseDraft.category_id" required><option value="">Seleccioná una categoría</option>@for (category of categories(); track category.id) { <option [value]="category.id">{{ category.name }}</option> }</select></label><p class="text-sm">{{ installmentsOnly ? 'Podés pagar cuotas completas o parcialmente. Los gastos se muestran por mes de vencimiento; los pagos descuentan saldo sin duplicar el gasto.' : 'La compra en el día del cierre entra en ese cierre; el vencimiento es posterior. Los gastos se muestran en el mes de vencimiento de cada cuota.' }}</p><div class="flex gap-3"><button class="btn-primary" [disabled]="form.invalid">Guardar compra</button><button type="button" (click)="formMode = ''">Cancelar</button></div>
      </fieldset></form></section>
    }
    @if (paying(); as installment) {
      <section class="finance-card mt-6 max-w-xl"><h2 class="text-xl font-bold">Pagar cuota {{ installment.number }} · {{ money(installment.amount) }}</h2><form #form="ngForm" (ngSubmit)="savePayment()" class="mt-4"><fieldset [disabled]="busy()" class="grid gap-4"><label>Cuenta de origen<select class="form-input" name="account" [(ngModel)]="paymentDraft.account_id" required><option value="">Seleccioná una cuenta</option>@for (account of accounts(); track account.id) { <option [value]="account.id">{{ account.name }} · {{ money(account.balance) }}</option> }</select></label>@if (!installment.card_name) { <label>Importe a pagar<input class="form-input" name="paidAmount" [(ngModel)]="paymentDraft.amount" inputmode="decimal" pattern="[0-9]+([.,][0-9]{1,2})?" required></label><p>Pendiente de esta cuota: {{ money(installment.pending_amount) }}</p> }<label>Fecha de pago<input class="form-input" type="date" name="paidDate" [(ngModel)]="paymentDraft.effective_date" required></label><div class="flex gap-3"><button class="btn-primary" [disabled]="form.invalid">Registrar pago</button><button type="button" (click)="paying.set(null)">Cancelar</button></div></fieldset></form></section>
    }
    <section class="finance-card mt-8"><h2 class="text-xl font-bold">Cuotas por mes de vencimiento</h2><div class="grid gap-3 mt-4 sm:grid-cols-2 xl:grid-cols-3">@for (month of monthlyTotals(); track month.month) { <div class="border rounded-xl p-3"><h3 class="font-bold">{{ month.month }}</h3><p>Total {{ money(month.total) }}</p><p>Pendiente {{ money(month.pending) }}</p></div> } @empty { <p>Sin cuotas registradas.</p> }</div></section>
    <section class="mt-8"><h2 class="text-2xl font-bold">Compras y cuotas</h2>
      @for (purchase of purchases(); track purchase.id) {
        <article class="finance-card mt-4"><h3 class="font-bold break-words">{{ purchase.description }}</h3><p>{{ purchase.creditor || purchase.purchase_date }} · Total {{ money(purchase.amount) }} · Pendiente {{ money(purchase.pending_amount) }}</p><div class="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">@for (installment of purchase.installments; track installment.id) { <div class="border rounded-xl p-3"><p class="font-semibold">{{ installment.card_name || 'Sin tarjeta' }} · Cuota {{ installment.number }}/{{ installment.installments_count }}</p><p>{{ money(installment.amount) }} · Vence {{ installment.due_date }}</p>@if (installment.closing_date) { <p class="text-sm">Cierre {{ installment.closing_date }}</p> }<p class="text-sm">{{ installment.status === 'paid' ? 'Pagada' : installment.status === 'partial' ? 'Pago parcial' : 'Obligación pendiente' }} · Pendiente {{ money(installment.pending_amount) }}</p>@if (installment.payment_id) { <p class="text-brand-700">Pagada {{ installment.paid_date }} desde {{ installment.account_name }}</p> } @if (installment.status !== 'paid') { <button class="underline mt-2" [disabled]="busy()" (click)="pay(installment)">Pagar cuota</button> }@for (payment of installment.payments; track payment.id) { <p class="mt-2 text-sm text-brand-700">Pago efectuado: {{ money(payment.amount) }} · {{ payment.effective_date }} · {{ payment.account_name }}</p> }</div> }</div></article>
      } @empty { <p class="mt-4">Registrá una compra para consultar sus cuotas y lo que falta pagar.</p> }
    </section>
  `,
})
export class CardsPageComponent {
  readonly installmentsOnly = !!inject(ActivatedRoute).snapshot.data['installmentsOnly'];
  readonly auth = inject(AuthService); readonly finance = inject(FinanceService); readonly money = money;
  readonly cards = signal<CreditCard[]>([]); readonly purchases = signal<CardPurchase[]>([]); readonly categories = signal<Category[]>([]); readonly accounts = signal<FinancialAccount[]>([]);
  readonly loading = signal(false); readonly busy = signal(false); readonly error = signal(''); readonly success = signal(''); readonly paying = signal<CardInstallment | null>(null);
  formMode = ''; editingId = ''; private version = 0; private retry = { fingerprint: '', key: '' };
  cardDraft = { bank: '', name: '', closing_day: 25, due_day: 10 };
  purchaseDraft = { card_id: '', category_id: '', description: '', amount: '', purchase_date: localDate(), installments_count: 1, creditor: '', first_due_date: localDate() };
  paymentDraft = { account_id: '', effective_date: localDate(), amount: '' };
  constructor() { effect(() => { const home = this.auth.activeHousehold()?.id; ++this.version; this.cards.set([]); this.purchases.set([]); this.accounts.set([]); this.categories.set([]); this.formMode = ''; this.paying.set(null); this.error.set(''); this.success.set(''); this.retry = { fingerprint: '', key: '' }; if (home) void this.load(); }); }
  monthlyTotals(): { month: string; total: string; pending: string }[] {
    const totals = new Map<string, { total: bigint; pending: bigint }>();
    for (const purchase of this.purchases()) for (const installment of purchase.installments) {
      const month = installment.due_date.slice(0, 7);
      const amount = BigInt(installment.amount.replace('.', ''));
      const row = totals.get(month) ?? { total: 0n, pending: 0n };
      row.total += amount;
      row.pending += cents(installment.pending_amount);
      totals.set(month, row);
    }
    const decimal = (value: bigint): string => `${value / 100n}.${String(value % 100n).padStart(2, '0')}`;
    return [...totals.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([month, row]) => ({ month, total: decimal(row.total), pending: decimal(row.pending) }));
  }
  canManage(): boolean { return ['owner', 'admin'].includes(this.auth.activeHousehold()?.role ?? ''); }
  async load(): Promise<void> { const version = ++this.version; this.loading.set(true); try { const [cards, purchases, accounts, categories] = await Promise.all([this.finance.all<CreditCard>('credit-cards'), this.finance.all<CardPurchase>('card-purchases'), this.finance.all<FinancialAccount>('accounts'), this.finance.all<Category>('categories')]); if (version !== this.version) return; this.cards.set(cards); this.purchases.set(purchases.filter(p => this.installmentsOnly ? !p.card_id : !!p.card_id)); this.accounts.set(accounts.filter(a => a.is_active)); this.categories.set(categories.filter(c => c.is_active && c.type === 'expense')); } catch (error) { if (version === this.version) this.error.set(financeError(error)); } finally { if (version === this.version) this.loading.set(false); } }
  edit(card?: CreditCard): void { this.editingId = card?.id ?? ''; this.cardDraft = { bank: card?.bank ?? '', name: card?.name ?? '', closing_day: card?.closing_day ?? 25, due_day: card?.due_day ?? 10 }; this.formMode = 'card'; this.paying.set(null); this.retry = { fingerprint: '', key: '' }; }
  buy(card?: CreditCard): void { this.purchaseDraft = { card_id: card?.id ?? '', category_id: '', description: '', amount: '', purchase_date: localDate(), installments_count: 1, creditor: '', first_due_date: localDate() }; this.formMode = 'purchase'; this.paying.set(null); this.retry = { fingerprint: '', key: '' }; }
  pay(installment: CardInstallment): void { this.paying.set(installment); this.paymentDraft = { account_id: '', effective_date: localDate(), amount: installment.pending_amount }; this.formMode = ''; this.retry = { fingerprint: '', key: '' }; }
  saveCard(): Promise<void> { return this.submit(this.editingId ? `credit-cards/${this.editingId}/` : 'credit-cards/', this.cardDraft, !!this.editingId); }
  savePurchase(): Promise<void> { return this.submit('card-purchases/', { ...this.purchaseDraft, card_id: this.purchaseDraft.card_id || null, first_due_date: this.installmentsOnly ? this.purchaseDraft.first_due_date : null, amount: this.purchaseDraft.amount.replace(',', '.') }); }
  savePayment(): Promise<void> { return this.submit(`card-installments/${this.paying()?.id}/pay/`, this.paying()?.card_name ? { account_id: this.paymentDraft.account_id, effective_date: this.paymentDraft.effective_date } : { ...this.paymentDraft, amount: this.paymentDraft.amount.replace(',', '.') }); }
  archive(card: CreditCard): Promise<void> { return this.submit(`credit-cards/${card.id}/`, { is_active: !card.is_active }, true); }
  private async submit(path: string, payload: unknown, patch = false): Promise<void> { if (this.busy()) return; const home = this.auth.activeHousehold()?.id; const fingerprint = JSON.stringify({ path, payload, home }); if (this.retry.fingerprint !== fingerprint) this.retry = { fingerprint, key: crypto.randomUUID() }; this.busy.set(true); this.error.set(''); this.success.set(''); try { await this.finance.write(path, payload, this.retry.key, patch); if (home !== this.auth.activeHousehold()?.id) return; this.formMode = ''; this.paying.set(null); this.retry = { fingerprint: '', key: '' }; this.success.set('Guardado correctamente.'); await this.load(); } catch (error) { if (home === this.auth.activeHousehold()?.id) this.error.set(financeError(error)); } finally { this.busy.set(false); } }
}
