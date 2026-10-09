import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { Category, FinanceService, FinancialAccount, History, Operation, Page, financeError, money } from '../../core/finance.service';
import { OperationFormComponent } from './operation-form.component';

@Component({
  imports: [FormsModule, OperationFormComponent],
  template: `
    <header class="flex flex-wrap justify-between gap-4"><div><p class="text-sm text-brand-700">{{ auth.activeHousehold()?.name }}</p><h1 class="text-3xl font-black">Movimientos</h1></div><button class="btn-primary" (click)="editing.set(null); showForm.set(true)">Registrar movimiento</button></header>
    @if (error()) { <p class="notice-error" role="alert">{{ error() }}</p> }
    @if (showForm()) { <section class="finance-card mt-6 max-w-2xl"><div class="flex justify-between"><h2 class="font-bold text-xl">{{ editing() ? 'Corregir movimiento' : 'Nuevo movimiento' }}</h2><button (click)="showForm.set(false)">Cerrar</button></div><gst-operation-form [operation]="editing()" (saved)="showForm.set(false); load()" /></section> }
    <form class="finance-card mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4" (ngSubmit)="page = 1; load()">
      <label>Desde<input class="form-input" type="date" name="from" [(ngModel)]="filters['from']"></label><label>Hasta<input class="form-input" type="date" name="to" [(ngModel)]="filters['to']"></label>
      <label>Tipo<select class="form-input" name="type" [(ngModel)]="filters['type']"><option value="">Todos</option><option value="expense">Gastos</option><option value="income">Ingresos</option><option value="transfer">Transferencias</option><option value="opening">Aperturas</option></select></label>
      <label>Cuenta<select class="form-input" name="account" [(ngModel)]="filters['account']"><option value="">Todas</option>@for (account of accounts(); track account.id) { <option [value]="account.id">{{ account.name }}</option> }</select></label>
      <label>Categoría<select class="form-input" name="category" [(ngModel)]="filters['category']"><option value="">Todas</option>@for (category of categories(); track category.id) { <option [value]="category.id">{{ category.name }}</option> }</select></label>
      <label>Buscar<input class="form-input" name="search" [(ngModel)]="filters['search']" maxlength="200" placeholder="Descripción"></label>
      <label>Estado<select class="form-input" name="status" [(ngModel)]="filters['status']"><option value="">Todos</option><option value="posted">Vigentes</option><option value="voided">Anulados</option></select></label>
      <label>Orden<select class="form-input" name="ordering" [(ngModel)]="filters['ordering']"><option value="-effective_date">Más recientes</option><option value="effective_date">Más antiguos</option><option value="-amount">Mayor importe</option><option value="amount">Menor importe</option></select></label><button class="btn-primary" [disabled]="loading()">Aplicar filtros</button>
    </form>
    @if (loading()) { <p class="mt-6" role="status">Cargando movimientos…</p> }
    <section class="mt-6 grid gap-3">
      @for (operation of data()?.results; track operation.id) {
        <article class="finance-card flex flex-wrap items-start justify-between gap-4" [class.opacity-60]="operation.status === 'voided'"><div class="min-w-0"><p class="text-sm text-slate-500">{{ operation.effective_date }} · {{ labels[operation.type] }} {{ operation.status === 'voided' ? '· Anulado' : '' }}</p><h2 class="font-bold break-words">{{ operation.description || operation.category_name || labels[operation.type] }}</h2><p>{{ operation.account_name }}{{ operation.destination_name ? ' → ' + operation.destination_name : '' }}</p><p class="text-sm text-slate-500">{{ operation.category_name }} · {{ operation.creator_name }}</p></div><div><p class="text-xl font-bold" [class.text-red-600]="operation.type === 'expense'" [class.text-brand-700]="operation.type === 'income'">{{ operation.type === 'expense' ? '−' : operation.type === 'income' ? '+' : '' }}{{ money(operation.amount) }} ARS</p><div class="mt-3 flex gap-3 text-sm">@if (operation.can_edit) { <button class="underline" (click)="editing.set(operation); showForm.set(true)">Corregir</button><button class="underline" [disabled]="busy()" (click)="voidOperation(operation)">Anular</button> }<button class="underline" (click)="history(operation)">Historial</button></div></div></article>
      } @empty { @if (!loading()) { <div class="finance-card"><h2 class="font-bold">No hay movimientos para estos filtros</h2><p>Registrá un ingreso, un gasto o una transferencia para empezar.</p></div> } }
    </section>
    <div class="mt-5 flex justify-between gap-2"><button [disabled]="!data()?.previous || loading()" (click)="page = page - 1; load()">Anterior</button><p>Página {{ page }} · {{ data()?.count ?? 0 }} movimientos</p><button [disabled]="!data()?.next || loading()" (click)="page = page + 1; load()">Siguiente</button></div>
    @if (events()) { <section class="finance-card mt-6"><div class="flex justify-between"><h2 class="font-bold">Historial de {{ historyTitle() }}</h2><button (click)="events.set(null)">Cerrar</button></div>@for (event of events(); track event.created_at) { <div class="mt-3 border-t pt-3"><p>{{ event.action }} · {{ event.actor_name }} · {{ event.created_at }}</p><pre class="overflow-auto text-xs mt-2">{{ formatHistory(event) }}</pre></div> }<button [disabled]="!historyNext()" (click)="moreHistory()">Más eventos</button></section> }
  `, changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TransactionsPageComponent {
  readonly auth = inject(AuthService); private readonly finance = inject(FinanceService); private readonly route = inject(ActivatedRoute);
  readonly data = signal<Page<Operation> | null>(null); readonly accounts = signal<FinancialAccount[]>([]); readonly categories = signal<Category[]>([]); readonly loading = signal(false); readonly busy = signal(false); readonly error = signal(''); readonly showForm = signal(false); readonly editing = signal<Operation | null>(null); readonly events = signal<History[] | null>(null); readonly historyTitle = signal(''); readonly historyNext = signal(false);
  readonly labels: Record<string, string> = { opening: 'Apertura', expense: 'Gasto', income: 'Ingreso', transfer: 'Transferencia' }; readonly money = money;
  page = 1; filters: Record<string, string> = { from: '', to: '', type: '', account: this.route.snapshot.queryParamMap.get('account') ?? '', category: '', status: '', search: '', ordering: '-effective_date' };
  private historyId = ''; private historyPage = 1; private loadVersion = 0;
  constructor() { effect(() => { const household = this.auth.activeHousehold()?.id; this.data.set(null); this.events.set(null); this.showForm.set(false); this.accounts.set([]); this.categories.set([]); this.error.set(''); this.page = 1; if (household) { void this.load(); void this.options(household); } }); }
  async options(household: string): Promise<void> { try { const [accounts, categories] = await Promise.all([this.finance.all<FinancialAccount>('accounts'), this.finance.all<Category>('categories')]); if (household !== this.auth.activeHousehold()?.id) return; this.accounts.set(accounts); this.categories.set(categories); } catch (error) { this.error.set(financeError(error)); } }
  async load(): Promise<void> { const version = ++this.loadVersion; this.loading.set(true); this.error.set(''); try { const data = await this.finance.list<Operation>('transactions', { ...this.filters, page: String(this.page) }); if (version === this.loadVersion) this.data.set(data); } catch (error) { if (version === this.loadVersion) this.error.set(financeError(error)); } finally { if (version === this.loadVersion) this.loading.set(false); } }
  async voidOperation(operation: Operation): Promise<void> { if (this.busy() || !confirm('¿Anular este movimiento? Se conservará en el historial.')) return; this.busy.set(true); try { await this.finance.write(`transactions/${operation.id}/void/`, { expected_revision: operation.revision }, crypto.randomUUID()); await this.load(); } catch (error) { this.error.set(financeError(error)); } finally { this.busy.set(false); } }
  async history(operation: Operation): Promise<void> { this.historyId = operation.id; this.historyPage = 0; this.historyTitle.set(operation.description || this.labels[operation.type]); this.events.set([]); await this.moreHistory(); }
  async moreHistory(): Promise<void> { try { const data = await this.finance.read<Page<History>>(`transactions/${this.historyId}/history/`, { page: String(++this.historyPage) }); this.events.update(events => [...(events ?? []), ...data.results]); this.historyNext.set(!!data.next); } catch (error) { this.error.set(financeError(error)); } }
  formatHistory(event: History): string { return JSON.stringify({ antes: event.before, después: event.after }, null, 2); }
}
