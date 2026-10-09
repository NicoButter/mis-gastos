import { HttpClient, HttpHeaders, HttpParams, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { AuthService } from './auth.service';

export interface FinancialAccount { id: string; name: string; kind: string; currency: string; description: string; is_active: boolean; balance: string; usage_count?: number; }
export interface Category { id: string; name: string; type: string; slug: string; is_active: boolean; color: string; usage_count?: number; }
export interface Operation { id: string; type: string; amount: string; currency: string; effective_date: string; description: string; account_id: string; destination_id: string | null; category_id: string | null; account_name: string; destination_name: string | null; category_name: string | null; creator_name: string; status: string; revision: number; can_edit: boolean; }
export interface Page<T> { count: number; next: string | null; previous: string | null; results: T[]; }
export interface Summary { currency: string; month: string; balance: string; income: string; expense: string; net: string; count: number; accounts: FinancialAccount[]; recent: Operation[]; distribution: { name: string; amount: string }[]; }
export interface History { action: string; actor_name: string; before: Record<string, unknown>; after: Record<string, unknown>; created_at: string; }

export function localDate(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

export function money(value: string): string {
  const negative = value.startsWith('-');
  const [whole, fraction = '00'] = value.replace(/^-/, '').split('.');
  const formatted = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(BigInt(whole || '0'));
  return (negative ? '−' : '') + formatted.replace(/,00$/, ',' + fraction.padEnd(2, '0').slice(0, 2));
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
  async all<T>(resource: string): Promise<T[]> {
    const household = this.auth.activeHousehold()?.id;
    const result: T[] = [];
    for (let page = 1; ; page++) {
      const response = await this.list<T>(resource, { page: String(page), page_size: '100' });
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
