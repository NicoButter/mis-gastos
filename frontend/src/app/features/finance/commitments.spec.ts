import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { vi } from 'vitest';
import { AuthService } from '../../core/auth.service';
import { CardInstallment, FinanceService, RecurringOccurrence } from '../../core/finance.service';
import { CardsPageComponent } from './cards-page.component';
import { RecurringPageComponent } from './recurring-page.component';

const installment: CardInstallment = { id: 'installment', number: 1, amount: '30.01', pending_amount: '20.01', paid_amount: '10.00', closing_date: '', due_date: '2026-10-31', card_name: null, description: 'Bicicleta', installments_count: 3, payment_id: null, paid_date: null, account_name: null, status: 'partial', payments: [] };
const occurrence: RecurringOccurrence = { id: 'occurrence', recurring_id: 'rule', name: 'Netflix', amount: '12.50', due_date: '2026-10-15', status: 'pending', account_id: 'account', payment_id: null, paid_date: null, account_name: null };

describe('financed and recurring commitments', () => {
  let auth: { activeHousehold: ReturnType<typeof signal<{ id: string; name: string }>> };
  let finance: { all: ReturnType<typeof vi.fn>; write: ReturnType<typeof vi.fn> };
  beforeEach(() => {
    auth = { activeHousehold: signal({ id: 'home-a', name: 'Hogar A' }) };
    finance = { all: vi.fn(async () => []), write: vi.fn(async () => ({})) };
    TestBed.configureTestingModule({ providers: [{ provide: AuthService, useValue: auth }, { provide: FinanceService, useValue: finance }, { provide: ActivatedRoute, useValue: { snapshot: { data: { installmentsOnly: true } } } }] });
  });
  it('reuses purchases without a card and submits partial amounts as exact decimals', async () => {
    const fixture = TestBed.createComponent(CardsPageComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance;
    component.buy(); component.purchaseDraft.description = 'Bicicleta'; component.purchaseDraft.amount = '90,01'; component.purchaseDraft.installments_count = 3; component.purchaseDraft.first_due_date = '2026-10-31'; component.purchaseDraft.category_id = 'category';
    await component.savePurchase();
    expect(finance.write).toHaveBeenCalledWith('card-purchases/', expect.objectContaining({ card_id: null, amount: '90.01', first_due_date: '2026-10-31' }), expect.any(String), false);
    component.pay(installment); expect(component.paymentDraft.amount).toBe('20.01'); component.paymentDraft.account_id = 'account'; component.paymentDraft.amount = '10,25'; await component.savePayment();
    expect(finance.write).toHaveBeenLastCalledWith('card-installments/installment/pay/', expect.objectContaining({ amount: '10.25', account_id: 'account' }), expect.any(String), false);
  });
  it('retains a key after a failed payment and clears context when the household changes', async () => {
    const fixture = TestBed.createComponent(CardsPageComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.pay(installment); component.paymentDraft.account_id = 'account';
    finance.write.mockRejectedValueOnce(new Error('offline')); await component.savePayment(); const key = finance.write.mock.calls[0][2]; await component.savePayment(); expect(finance.write.mock.calls[1][2]).toBe(key);
    component.buy(); auth.activeHousehold.set({ id: 'home-b', name: 'Hogar B' }); fixture.detectChanges(); await fixture.whenStable();
    expect(component.formMode).toBe(''); expect(component.purchases()).toEqual([]); expect(component.paying()).toBeNull();
  });
  it('changes only one occurrence and confirms using its optional account', async () => {
    const fixture = TestBed.createComponent(RecurringPageComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.select(occurrence, 'amount'); component.occurrenceAmount = '15,05'; await component.submitOccurrence();
    expect(finance.write).toHaveBeenCalledWith('recurring-occurrences/occurrence/', { amount: '15.05' }, expect.any(String), true);
    component.select(occurrence, 'pay'); await component.submitOccurrence();
    expect(finance.write).toHaveBeenLastCalledWith('recurring-occurrences/occurrence/pay/', expect.objectContaining({ account_id: 'account' }), expect.any(String), false);
  });
  it('clears recurrence and occurrence context on household change', async () => {
    const fixture = TestBed.createComponent(RecurringPageComponent); fixture.detectChanges(); await fixture.whenStable();
    const component = fixture.componentInstance; component.create(); component.select(occurrence, 'pay');
    auth.activeHousehold.set({ id: 'home-b', name: 'Hogar B' }); fixture.detectChanges(); await fixture.whenStable();
    expect(component.selected()).toBeNull(); expect(component.rules()).toEqual([]); expect(component.showForm()).toBe(false);
  });
});
