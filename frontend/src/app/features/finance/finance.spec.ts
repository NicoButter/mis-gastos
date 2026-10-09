import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { AuthService } from '../../core/auth.service';
import { FinanceService, FinancialAccount, Operation, Summary } from '../../core/finance.service';
import { OperationFormComponent } from './operation-form.component';
import { AccountsPageComponent } from './accounts-page.component';
import { DashboardPageComponent } from '../home/dashboard-page.component';

const account: FinancialAccount = { id: 'account-a', name: 'Efectivo', kind: 'cash', currency: 'ARS', description: '', is_active: true, balance: '0.00' };
const operation: Operation = { id: 'operation-a', type: 'expense', amount: '10.25', currency: 'ARS', effective_date: '2026-10-09', description: '', account_id: account.id, destination_id: null, category_id: 'expense-a', account_name: account.name, destination_name: null, category_name: 'Alimentos', creator_name: 'Persona', status: 'posted', revision: 1, can_edit: true };
const emptySummary: Summary = { currency: 'ARS', month: '2026-10', balance: '0.00', income: '0.00', expense: '0.00', net: '0.00', count: 0, accounts: [], recent: [], distribution: [] };

describe('financial screens', () => {
  let auth: { activeHousehold: ReturnType<typeof signal<{id: string; name: string} | null>> };
  let finance: { all: ReturnType<typeof vi.fn>; write: ReturnType<typeof vi.fn>; read: ReturnType<typeof vi.fn>; changed: ReturnType<typeof signal<number>> };
  beforeEach(() => {
    auth = { activeHousehold: signal({ id: 'home-a', name: 'Hogar A' }) };
    finance = { all: vi.fn(async (resource: string) => resource === 'accounts' ? [account, { ...account, id: 'account-b', name: 'Banco' }] : [{ id: 'expense-a', name: 'Alimentos', type: 'expense', is_active: true }, { id: 'income-a', name: 'Sueldo', type: 'income', is_active: true }]), write: vi.fn(async () => operation), read: vi.fn(async () => emptySummary), changed: signal(0) };
    TestBed.configureTestingModule({ providers: [provideRouter([]), { provide: AuthService, useValue: auth }, { provide: FinanceService, useValue: finance }] });
  });

  it('creates an account with a decimal opening balance', async () => {
    const fixture = TestBed.createComponent(AccountsPageComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.edit(); component.draft.name = 'Banco'; component.draft.opening_balance = '100,25'; await component.save();
    expect(finance.write).toHaveBeenCalledWith('accounts/', expect.objectContaining({ opening_balance: '100.25', name: 'Banco' }), expect.any(String), false);
  });

  it.each(['expense', 'income', 'transfer'])('registers a real %s request', async type => {
    const fixture = TestBed.createComponent(OperationFormComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.draft = { type, amount: '10,25', account_id: account.id, category_id: type === 'income' ? 'income-a' : 'expense-a', destination_id: 'account-b', effective_date: '2026-10-09', description: 'Real' };
    await component.save();
    expect(finance.write).toHaveBeenCalledWith(type === 'transfer' ? 'transfers/' : 'transactions/', expect.objectContaining({ amount: '10.25', type, destination_id: type === 'transfer' ? 'account-b' : null }), expect.any(String), false);
  });

  it('rejects zero, excessive precision and transfers to the same account', async () => {
    const fixture = TestBed.createComponent(OperationFormComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.draft.account_id = account.id; component.draft.category_id = 'expense-a';
    for (const amount of ['0', '-1', '1.001']) { component.draft.amount = amount; await component.save(); }
    component.draft.amount = '10'; component.draft.type = 'transfer'; component.draft.destination_id = account.id; await component.save();
    expect(finance.write).not.toHaveBeenCalled();
  });

  it('blocks double submission and retains its key for an identical retry', async () => {
    const fixture = TestBed.createComponent(OperationFormComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.draft.amount = '10'; component.draft.account_id = account.id; component.draft.category_id = 'expense-a';
    let fail!: (reason: Error) => void; finance.write.mockImplementationOnce(() => new Promise((_resolve, reject) => { fail = reject; }));
    const first = component.save(); await component.save(); expect(finance.write).toHaveBeenCalledTimes(1); const key = finance.write.mock.calls[0][2];
    fail(new Error('Offline')); await first; expect(component.error()).toContain('reintentá'); await component.save(); expect(finance.write.mock.calls[1][2]).toBe(key);
  });

  it('quick mode shows the expense flow and confirmation without navigating', async () => {
    const fixture = TestBed.createComponent(OperationFormComponent); fixture.componentRef.setInput('quick', true); fixture.detectChanges(); await fixture.whenStable();
    expect(fixture.nativeElement.textContent).toContain('Guardar gasto'); expect(fixture.nativeElement.querySelector('select[name="type"]')).toBeNull();
    const component = fixture.componentInstance; component.draft.amount = '10'; component.draft.account_id = account.id; component.draft.category_id = 'expense-a'; await component.save();
    expect(component.success()).toContain('Podés registrar otro'); expect(component.draft.amount).toBe('');
  });

  it('displays an empty dashboard with actual zeros and refreshes after writes', async () => {
    const fixture = TestBed.createComponent(DashboardPageComponent); fixture.detectChanges(); await fixture.whenStable(); fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Todavía no hay cuentas'); expect(fixture.nativeElement.textContent).toContain('$ 0,00');
    finance.read.mockResolvedValue({ ...emptySummary, income: '250.00' }); finance.changed.update(n => n + 1); fixture.detectChanges(); await fixture.whenStable();
    expect(fixture.componentInstance.summary()?.income).toBe('250.00');
  });

  it('clears financial data and resets form context on household change', async () => {
    const fixture = TestBed.createComponent(OperationFormComponent); fixture.detectChanges(); await fixture.whenStable(); fixture.componentInstance.draft.account_id = account.id;
    finance.all.mockResolvedValue([]); auth.activeHousehold.set({ id: 'home-b', name: 'Hogar B' }); fixture.detectChanges(); await fixture.whenStable();
    expect(fixture.componentInstance.accounts()).toEqual([]); expect(fixture.componentInstance.draft.account_id).toBe('');
  });
});
