import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/auth.service';
import { Category, FinanceService, financeError } from '../../core/finance.service';

@Component({
  imports: [FormsModule],
  template: `<h1 class="text-3xl font-black">Categorías</h1><p class="mt-2">Categorías propias de {{ auth.activeHousehold()?.name }}. Desactivar conserva el historial.</p>
    @if (error()) { <p class="notice-error" role="alert">{{ error() }}</p> } @if (success()) { <p class="notice-success" role="status">{{ success() }}</p> }
    @if (canManage()) { <form #form="ngForm" (ngSubmit)="save()" class="finance-card mt-6 grid gap-4 max-w-xl"><h2 class="font-bold">{{ editingId ? 'Editar categoría' : 'Nueva categoría' }}</h2><label>Nombre<input class="form-input" name="name" [(ngModel)]="draft.name" required maxlength="100"></label><label>Tipo<select class="form-input" name="type" [(ngModel)]="draft.type" [disabled]="!!editingId"><option value="expense">Gasto</option><option value="income">Ingreso</option></select></label><label>Color<input type="color" class="form-input h-12" name="color" [(ngModel)]="draft.color"></label><label><input type="checkbox" name="active" [(ngModel)]="draft.is_active"> Activa</label><button class="btn-primary" [disabled]="form.invalid || busy()">Guardar categoría</button>@if (editingId) { <button type="button" (click)="reset()">Cancelar edición</button> }</form> }
    <section class="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">@for (category of categories(); track category.id) { <article class="finance-card"><h2 class="font-bold">{{ category.name }}</h2><p>{{ category.type === 'expense' ? 'Gasto' : 'Ingreso' }} · {{ category.is_active ? 'Activa' : 'Inactiva' }}</p>@if (canManage()) { <button class="underline mt-3" (click)="edit(category)">Editar</button> }</article> }</section>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CategoriesPageComponent {
  readonly auth = inject(AuthService); private readonly finance = inject(FinanceService); readonly categories = signal<Category[]>([]); readonly busy = signal(false); readonly error = signal(''); readonly success = signal('');
  editingId = ''; draft = { name: '', type: 'expense', color: '#0f766e', is_active: true }; private retry = { fingerprint: '', key: '' };
  constructor() { effect(() => { const household = this.auth.activeHousehold()?.id; this.categories.set([]); this.reset(); if (household) void this.load(); }); }
  reset(): void { this.editingId = ''; this.draft = { name: '', type: 'expense', color: '#0f766e', is_active: true }; this.error.set(''); this.success.set(''); }
  edit(category: Category): void { this.editingId = category.id; this.draft = { name: category.name, type: category.type, color: category.color || '#0f766e', is_active: category.is_active }; }
  canManage(): boolean { return ['owner', 'admin'].includes(this.auth.activeHousehold()?.role ?? ''); }
  async load(): Promise<void> { try { this.categories.set(await this.finance.all<Category>('categories')); } catch (error) { this.error.set(financeError(error)); } }
  async save(): Promise<void> { if (this.busy()) return; const path = this.editingId ? `categories/${this.editingId}/` : 'categories/'; const fingerprint = JSON.stringify({ path, draft: this.draft, household: this.auth.activeHousehold()?.id }); if (this.retry.fingerprint !== fingerprint) this.retry = { fingerprint, key: crypto.randomUUID() }; this.busy.set(true); this.error.set(''); try { await this.finance.write(path, this.draft, this.retry.key, !!this.editingId); this.reset(); this.success.set('Categoría guardada.'); await this.load(); } catch (error) { this.error.set(financeError(error)); } finally { this.busy.set(false); } }
}
