import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { vi } from 'vitest';
import { AuthService } from '../../core/auth.service';
import { FinanceService, FinancialAccount, Operation, Summary } from '../../core/finance.service';
import { OperationFormComponent } from './operation-form.component';
import { TransactionsPageComponent } from './transactions-page.component';
import { AccountsPageComponent } from './accounts-page.component';
import { DashboardPageComponent } from '../home/dashboard-page.component';

const account: FinancialAccount = { id: 'account-a', name: 'Efectivo', kind: 'cash', currency: 'ARS', description: '', is_active: true, balance: '0.00' };
const operation: Operation = { id: 'operation-a', type: 'expense', amount: '10.25', currency: 'ARS', effective_date: '2026-10-09', description: '', account_id: account.id, destination_id: null, category_id: 'expense-a', account_name: account.name, destination_name: null, category_name: 'Alimentos', creator_name: 'Persona', status: 'posted', revision: 1, can_edit: true };
const emptySummary: Summary = { available_balances: [{ currency: 'ARS', amount: '0.00' }], currency: 'ARS', month: '2026-10', balance: '0.00', income: '0.00', expense: '0.00', net: '0.00', count: 0, accounts: [], recent: [], distribution: [] };

describe('financial screens', () => {
  let auth: { activeHousehold: ReturnType<typeof signal<{id: string; name: string} | null>> };
  let finance: { list: ReturnType<typeof vi.fn>; all: ReturnType<typeof vi.fn>; write: ReturnType<typeof vi.fn>; read: ReturnType<typeof vi.fn>; changed: ReturnType<typeof signal<number>> };
  beforeEach(() => {
    auth = { activeHousehold: signal({ id: 'home-a', name: 'Hogar A' }) };
    finance = { list: vi.fn(async () => ({count: 0, next: null, previous: null, results: []})), all: vi.fn(async (resource: string) => resource === 'accounts' ? [account, { ...account, id: 'account-b', name: 'Banco' }] : [{ id: 'expense-a', name: 'Alimentos', type: 'expense', is_active: true }, { id: 'income-a', name: 'Sueldo', type: 'income', is_active: true }]), write: vi.fn(async () => operation), read: vi.fn(async () => emptySummary), changed: signal(0) };
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
  it('locks inputs while saving and ignores an old household completion', async () => {
    const fixture = TestBed.createComponent(OperationFormComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.draft.amount = '10'; component.draft.account_id = account.id; component.draft.category_id = 'expense-a';
    let finish!: (value: Operation) => void;
    finance.write.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const request = component.save(); fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('fieldset').disabled).toBe(true);
    auth.activeHousehold.set({ id: 'home-b', name: 'Hogar B' }); fixture.detectChanges(); await fixture.whenStable();
    component.draft.amount = '42'; finish(operation); await request;
    expect(component.draft.amount).toBe('42'); expect(component.success()).toBe('');
  });

  it('rejects stale account and category selections', async () => {
    const fixture = TestBed.createComponent(OperationFormComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.draft.amount = '10'; component.draft.account_id = 'archived'; component.draft.category_id = 'expense-a';
    await component.save(); component.draft.account_id = account.id; component.draft.category_id = 'inactive'; await component.save();
    expect(finance.write).not.toHaveBeenCalled();
  });

  it('keeps a new household account form intact after an old write completes', async () => {
    const fixture = TestBed.createComponent(AccountsPageComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.edit(); component.draft.name = 'Old';
    let finish!: (value: Operation) => void; finance.write.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const request = component.save(); auth.activeHousehold.set({ id: 'home-b', name: 'Hogar B' }); fixture.detectChanges(); await fixture.whenStable();
    component.edit(); component.draft.name = 'New'; finish(operation); await request;
    expect(component.showForm()).toBe(true); expect(component.draft.name).toBe('New'); expect(component.success()).toBe('');
  });

  it('discards a pending audit history after switching households', async () => {
    const fixture = TestBed.createComponent(TransactionsPageComponent); fixture.detectChanges(); await fixture.whenStable();
    let finish!: (value: unknown) => void;
    finance.read.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const request = fixture.componentInstance.history(operation);
    auth.activeHousehold.set({ id: 'home-b', name: 'Hogar B' }); fixture.detectChanges(); await fixture.whenStable();
    finish({ count: 1, next: null, previous: null, results: [{ action: 'old-home', created_at: '2026-10-01', actor_name: 'Old', before: {}, after: {} }] });
    await request; expect(fixture.componentInstance.events()).toBeNull();
  });

  it('renders prominent available balance, monthly result and overspending from real summary fields', async () => {
    finance.read.mockResolvedValue({ ...emptySummary, balance: '999.00', available_balances: [{ currency: 'ARS', amount: '123.45' }], income: '100.00', expense: '150.25', net: '-50.25' });
    const fixture = TestBed.createComponent(DashboardPageComponent); fixture.detectChanges(); await fixture.whenStable(); fixture.detectChanges();
    const element: HTMLElement = fixture.nativeElement;
    expect(element.querySelector('[data-testid="available-balance"]')?.textContent).toContain('123,45');
    expect(element.querySelector('[data-testid="available-balance"]')?.textContent).not.toContain('999,00');
    expect(element.querySelector('[data-testid="monthly-income"]')?.textContent).toContain('100,00');
    expect(element.querySelector('[data-testid="monthly-expense"]')?.textContent).toContain('150,25');
    expect(element.querySelector('[data-testid="monthly-net"]')?.textContent).toContain('−$\u00a050,25');
    expect(element.querySelector('[role="progressbar"]')?.getAttribute('aria-valuetext')).toContain('150,25% · sobregasto');
    expect(element.textContent).toContain('Saldo actual');
  });

  it('changes dashboard period and ignores an older response while preserving the current balance', async () => {
    const fixture = TestBed.createComponent(DashboardPageComponent); fixture.detectChanges(); await fixture.whenStable();
    let finish!: (value: Summary) => void;
    finance.read.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const pending = fixture.componentInstance.load();
    finance.read.mockResolvedValue({ ...emptySummary, month: '2026-09', income: '42.10', available_balances: [{ currency: 'ARS', amount: '75.25' }] });
    fixture.componentInstance.changePeriod('2026-09'); await fixture.whenStable(); fixture.detectChanges();
    expect(finance.read).toHaveBeenLastCalledWith('dashboard/summary/', { month: '2026-09' });
    expect(fixture.componentInstance.summary()?.income).toBe('42.10');
    finish({ ...emptySummary, income: '999.00' }); await pending;
    expect(fixture.componentInstance.summary()?.income).toBe('42.10');
    finance.changed.update(value => value + 1); fixture.detectChanges(); await fixture.whenStable();
    expect(finance.read).toHaveBeenLastCalledWith('dashboard/summary/', { month: '2026-09' });
  });

  it('clears dashboard KPIs on household change and discards a stale response', async () => {
    const fixture = TestBed.createComponent(DashboardPageComponent); fixture.detectChanges(); await fixture.whenStable();
    let finish!: (value: Summary) => void;
    finance.read.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const pending = fixture.componentInstance.load();
    auth.activeHousehold.set({ id: 'home-b', name: 'Hogar B' }); fixture.detectChanges(); await fixture.whenStable();
    finish({ ...emptySummary, available_balances: [{ currency: 'ARS', amount: '999.99' }] }); await pending; fixture.detectChanges();
    expect(fixture.componentInstance.summary()?.available_balances[0].amount).toBe('0.00');
    expect(fixture.nativeElement.textContent).not.toContain('999,99');
  });

  it('shows account flows separately, selects one account and refreshes on month and writes', async () => {
    finance.all.mockResolvedValue([{ ...account, balance: '90.25', monthly_income: '100.00', monthly_expense: '10.00', monthly_inflow: '150.00', monthly_outflow: '60.00' }, { ...account, id: 'account-b', name: 'Banco' }]);
    const fixture = TestBed.createComponent(AccountsPageComponent); fixture.detectChanges(); await fixture.whenStable(); fixture.detectChanges();
    const component = fixture.componentInstance; const select = fixture.nativeElement.querySelector('select') as HTMLSelectElement; select.value = account.id; select.dispatchEvent(new Event('change')); await fixture.whenStable(); fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Entradas del mes'); expect(text).toContain('150,00');
    expect(text).toContain('Ingresos del mes'); expect(text).toContain('100,00');
    expect(text).toContain('Salidas del mes'); expect(text).toContain('60,00');
    expect(text).toContain('Gastos del mes'); expect(text).toContain('10,00');
    expect(fixture.nativeElement.querySelectorAll('article')).toHaveLength(1);
    component.changePeriod('2026-09'); await fixture.whenStable();
    expect(finance.all).toHaveBeenLastCalledWith('accounts', { month: '2026-09' });
    finance.changed.update(value => value + 1); fixture.detectChanges(); await fixture.whenStable();
    expect(finance.all).toHaveBeenLastCalledWith('accounts', { month: '2026-09' });
    finance.all.mockResolvedValue([]); auth.activeHousehold.set({ id: 'home-b', name: 'Hogar B' }); fixture.detectChanges(); await fixture.whenStable();
    expect(component.accounts()).toEqual([]); expect(component.selectedAccountId).toBe('');
  });

  it('discards account summaries from an older period', async () => {
    const fixture = TestBed.createComponent(AccountsPageComponent); fixture.detectChanges(); await fixture.whenStable();
    let finish!: (value: FinancialAccount[]) => void;
    finance.all.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; }));
    const pending = fixture.componentInstance.load();
    finance.all.mockResolvedValue([{ ...account, monthly_income: '42.00' }]);
    fixture.componentInstance.changePeriod('2026-08'); await fixture.whenStable();
    finish([{ ...account, monthly_income: '999.00' }]); await pending;
    expect(fixture.componentInstance.accounts()[0].monthly_income).toBe('42.00');
  });

});
