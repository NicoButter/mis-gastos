import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { AuthService } from './auth.service';
import { FinanceService, money } from './finance.service';

describe('FinanceService session requests', () => {
  const household = signal({ id: 'home-a' });
  beforeEach(() => { household.set({ id: 'home-a' }); TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting(), { provide: AuthService, useValue: { activeHousehold: household } }] }); });
  afterEach(() => TestBed.inject(HttpTestingController).verify());
  it('sends CSRF bootstrap, idempotency and expected household on writes', async () => {
    const service = TestBed.inject(FinanceService); const http = TestBed.inject(HttpTestingController);
    const pending = service.write('transactions/', { amount: '0.10' }, 'retry-key');
    http.expectOne('/api/v1/auth/csrf/').flush({ csrfToken: 'csrf' }); await Promise.resolve();
    const request = http.expectOne('/api/v1/transactions/'); expect(request.request.headers.get('Idempotency-Key')).toBe('retry-key'); expect(request.request.headers.get('X-Household-ID')).toBe('home-a'); request.flush({ id: 'created' });
    await pending; expect(service.changed()).toBe(1);
  });
  it('discards a response that belongs to the previous household', async () => {
    const service = TestBed.inject(FinanceService); const http = TestBed.inject(HttpTestingController);
    const pending = service.list('accounts'); const request = http.expectOne('/api/v1/accounts/'); household.set({ id: 'home-b' }); request.flush({ results: [{ id: 'foreign' }], next: null });
    await expect(pending).rejects.toThrow('El hogar cambió');
  });
  it('does not send a write when household changes during CSRF bootstrap', async () => {
    const service = TestBed.inject(FinanceService); const http = TestBed.inject(HttpTestingController);
    const pending = service.write('transactions/', {}, 'retry-key'); household.set({ id: 'home-b' }); http.expectOne('/api/v1/auth/csrf/').flush({});
    await expect(pending).rejects.toThrow('El hogar cambió'); http.expectNone('/api/v1/transactions/');
  });
  it('formats large monetary amounts without rounding away cents', () => {
    expect(money('9999999999999999.99')).toContain('9.999.999.999.999.999,99'); expect(money('-0.10')).toContain('−'); expect(money('-0.10')).toContain('0,10');
  });
});
