import { HttpClient, HttpHeaders, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { AuthService } from './auth.service';

export interface FinancialAccount { id: string; name: string; kind: string; currency: string; description: string; is_active: boolean; balance: string; usage_count?: number; month?: string; monthly_inflow?: string; monthly_outflow?: string; monthly_income?: string; monthly_expense?: string; monthly_opening?: string; monthly_transfer_in?: string; monthly_transfer_out?: string; monthly_card_payments?: string; }
export interface Category { id: string; name: string; type: string; slug: string; is_active: boolean; color: string; usage_count?: number; }
export interface Operation { id: string; type: string; amount: string; currency: string; effective_date: string; description: string; account_id: string; destination_id: string | null; category_id: string | null; account_name: string; destination_name: string | null; category_name: string | null; creator_name: string; status: string; revision: number; can_edit: boolean; }
export interface Page<T> { count: number; next: string | null; previous: string | null; results: T[]; }
export interface CreditCard { id: string; bank: string; name: string; closing_day: number; due_day: number; is_active: boolean; }
export interface CardInstallment { id: string; number: number; amount: string; closing_date: string; due_date: string; card_name: string | null; paid_amount: string; pending_amount: string; status: string; payments: { id: string; amount: string; effective_date: string; account_name: string; transaction_id: string }[]; description: string; installments_count: number; payment_id: string | null; paid_date: string | null; account_name: string | null; }
export interface CardPurchase { id: string; card_id: string | null; creditor: string; first_due_date: string | null; description: string; amount: string; purchase_date: string; installments_count: number; pending_amount: string; installments: CardInstallment[]; }
export interface RecurringOccurrence { id: string; recurring_id: string; name: string; amount: string; due_date: string; status: string; account_id: string | null; payment_id: string | null; paid_date: string | null; account_name: string | null; }
export interface RecurringExpense { id: string; name: string; category_id: string; amount: string; start_date: string; due_day: number; account_id: string | null; status: string; can_edit: boolean; occurrences: RecurringOccurrence[]; }
export interface Summary { upcoming_recurring?: RecurringOccurrence[]; available_balances: { currency: string; amount: string }[]; card_pending?: string; upcoming_installments?: CardInstallment[]; currency: string; month: string; balance: string; income: string; expense: string; net: string; count: number; accounts: FinancialAccount[]; recent: Operation[]; distribution: { name: string; amount: string }[]; }
export interface History { action: string; actor_name: string; before: Record<string, unknown>; after: Record<string, unknown>; created_at: string; }

export function localDate(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

export function money(value: string, currency = 'ARS'): string {
  const negative = value.startsWith('-');
  const [whole, fraction = '00'] = value.replace(/^-/, '').split('.');
  const parts = new Intl.NumberFormat('es-AR', { style: 'currency', currency, minimumFractionDigits: 2, maximumFractionDigits: 2 }).formatToParts(BigInt(whole || '0'));
  return (negative ? '−' : '') + parts.map(part => part.type === 'fraction' ? fraction.padEnd(2, '0').slice(0, 2) : part.value).join('');
}

export function cents(value: string): bigint {
  const [whole, fraction = ''] = value.replace(/^-/, '').split('.');
  const result = BigInt(whole || '0') * 100n + BigInt(fraction.padEnd(2, '0').slice(0, 2));
  return value.startsWith('-') ? -result : result;
}

export function spendingRatio(income: string, expense: string): { percent: string; width: number; overspent: boolean } | null {
  const incoming = cents(income), outgoing = cents(expense);
  if (incoming <= 0n) return null;
  const basisPoints = outgoing * 10000n / incoming;
  return { percent: `${basisPoints / 100n},${String(basisPoints % 100n).padStart(2, '0')}%`, width: Number(basisPoints > 10000n ? 10000n : basisPoints) / 100, overspent: outgoing > incoming };
}

export function financeError(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    const fields = error.error?.error?.fields;
    if (fields) return Object.entries(fields).map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`).join(' · ');
    if (error.status === 409) return 'La operación cambió o el reintento tiene otros datos. Recargá antes de continuar.';
    if (error.status === 403) return 'Tu rol no permite esta acción.';
    if (error.status === 404) return 'El recurso no está disponible en este hogar.';
  }
  return 'No se pudo completar la solicitud. Revisá la conexión y reintentá.';
}

@Injectable({ providedIn: 'root' })
export class FinanceService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  readonly changed = signal(0);
  async list<T>(resource: string, filters: Record<string, string> = {}): Promise<Page<T>> {
    return this.read<Page<T>>(`${resource}/`, filters);
  }
  async all<T>(resource: string, filters: Record<string, string> = {}): Promise<T[]> {
    const household = this.auth.activeHousehold()?.id;
    const result: T[] = [];
    for (let page = 1; ; page++) {
      const response = await this.list<T>(resource, { ...filters, page: String(page), page_size: '100' });
      if (household !== this.auth.activeHousehold()?.id) throw new Error('El hogar cambió.');
      result.push(...response.results);
      if (!response.next) return result;
    }
  }
  async read<T>(path: string, filters: Record<string, string> = {}): Promise<T> {
    const household = this.auth.activeHousehold()?.id;
    if (!household) throw new Error('Seleccioná un hogar.');
    const params = new HttpParams({ fromObject: Object.fromEntries(Object.entries(filters).filter(([, value]) => !!value)) });
    const headers = new HttpHeaders({ 'X-Household-ID': household });
    const result = await firstValueFrom(this.http.get<T>(`/api/v1/${path}`, { params, headers }));
    if (household !== this.auth.activeHousehold()?.id) throw new Error('El hogar cambió.');
    return result;
  }
  async write<T>(path: string, payload: unknown, key: string, patch = false): Promise<T> {
    const household = this.auth.activeHousehold()?.id;
    await firstValueFrom(this.http.get('/api/v1/auth/csrf/'));
    if (!household || household !== this.auth.activeHousehold()?.id) throw new Error('El hogar cambió.');
    const headers = new HttpHeaders({ 'Idempotency-Key': key, 'X-Household-ID': household });
    const result = await firstValueFrom(patch ? this.http.patch<T>(`/api/v1/${path}`, payload, { headers }) : this.http.post<T>(`/api/v1/${path}`, payload, { headers }));
    this.changed.update(value => value + 1);
    if (household !== this.auth.activeHousehold()?.id) throw new Error('El hogar cambió.');
    return result;
  }
}
