import { expect, test } from '@playwright/test';
import { isolateHousehold } from './household';

test('dashboard hierarchy, current balance, monthly navigation and account flows', async ({ page }, testInfo) => {
  await isolateHousehold(page, 'Dashboard E2E');
  await page.goto('/app/accounts');
  for (const [name, opening] of [['Efectivo panel', '100,25'], ['Banco panel', '0']]) {
    await page.getByRole('button', { name: 'Agregar cuenta' }).click();
    await page.getByLabel('Nombre', { exact: true }).fill(name);
    await page.getByLabel('Saldo inicial').fill(opening);
    await page.getByLabel('Fecha de apertura').fill('2026-09-01');
    await page.getByRole('button', { name: 'Guardar cuenta' }).click();
    await expect(page.getByText('Cuenta guardada.')).toBeVisible();
  }
  await page.goto('/app/transactions');
  for (const [kind, amount] of [['income', '120,10'], ['expense', '50,05'], ['transfer', '30']]) {
    await page.getByRole('button', { name: 'Registrar movimiento' }).click();
    await page.getByRole('combobox', { name: 'Operación', exact: true }).selectOption(kind);
    await page.getByLabel('Importe · ARS').fill(amount);
    await page.getByLabel('Fecha', { exact: true }).fill('2026-10-10');
    if (kind !== 'transfer') await page.locator('fieldset button[aria-pressed]').first().click();
    await page.getByRole('combobox', { name: kind === 'income' ? 'Cuenta de destino' : 'Cuenta de origen', exact: true }).selectOption({ label: 'Efectivo panel' });
    if (kind === 'transfer') await page.getByRole('combobox', { name: 'Cuenta de destino', exact: true }).selectOption({ label: 'Banco panel' });
    await page.getByLabel('Descripción opcional').fill(`Panel ${kind}`);
    await page.getByRole('button', { name: kind === 'income' ? 'Guardar ingreso' : kind === 'expense' ? 'Guardar gasto' : 'Guardar transferencia' }).click();
    await expect(page.getByRole('heading', { name: `Panel ${kind}`, exact: true })).toBeVisible();
  }
  const { csrfToken } = await (await page.request.get('/api/v1/auth/csrf/')).json();
  const categories = await (await page.request.get('/api/v1/categories/?type=expense')).json();
  const purchase = await page.request.post('/api/v1/card-purchases/', {
    headers: { 'X-CSRFToken': csrfToken, 'Idempotency-Key': crypto.randomUUID() },
    data: { description: 'Bicicleta panel', amount: '90.00', installments_count: 3, creditor: 'Bicicletería', first_due_date: '2026-11-10', category_id: categories.results[0].id },
  });
  expect(purchase.status()).toBe(201);
  await page.goto('/app');
  await page.getByLabel('Mes', { exact: true }).fill('2026-10');
  await expect(page.getByTestId('available-balance')).toContainText('170,30');
  await expect(page.getByTestId('monthly-income')).toContainText('120,10');
  await expect(page.getByTestId('monthly-expense')).toContainText('50,05');
  await expect(page.locator('.dashboard-kpis > article')).toHaveCount(3);
  await expect(page.getByTestId('monthly-income').getByTestId('account-income')).toHaveCount(2);
  await expect(page.getByTestId('monthly-income')).toContainText('Efectivo panel');
  await expect(page.getByTestId('monthly-income')).toContainText('Banco panel');
  await expect(page.getByRole('heading', { name: 'Compras en cuotas', exact: true })).toBeVisible();
  const purchaseRow = page.getByTestId('installment-purchase');
  await expect(purchaseRow).toHaveCount(1);
  await expect(purchaseRow).toContainText('Bicicleta panel');
  await expect(purchaseRow).toContainText('0 de 3 cuotas pagadas · 3 pendientes');
  await expect(purchaseRow).toContainText('Total de la compra$ 90,00');
  await expect(purchaseRow).toContainText('Total pagado$ 0,00');
  await expect(purchaseRow).toContainText('Total pendiente$ 90,00');
  await expect(page.getByRole('heading', { name: 'Cuentas y saldos' })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Gastos por categoría' })).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('dashboard.png'), fullPage: true });
  await page.getByRole('button', { name: 'Mes anterior' }).click();
  await expect(page.getByLabel('Mes', { exact: true })).toHaveValue('2026-09');
  await expect(page.getByTestId('monthly-income').locator('.kpi-amount')).toContainText('100,25');
  await expect(page.getByTestId('monthly-expense')).toContainText('0,00');
  await expect(page.getByTestId('available-balance')).toContainText('170,30');
  await page.getByRole('button', { name: 'Mes siguiente' }).click();
  await expect(page.getByTestId('monthly-income')).toContainText('120,10');
  await page.goto('/app/accounts');
  await page.getByLabel('Mes', { exact: true }).fill('2026-10');
  await page.getByLabel('Consultar cuenta').selectOption({ label: 'Banco panel' });
  const bank = page.locator('article');
  await expect(bank).toHaveCount(1);
  await expect(bank).toContainText('Saldo actual');
  await expect(bank.locator('dl').first()).toContainText('Entradas del mes$ 30,00');
  await expect(bank.locator('dl').first()).toContainText('Ingresos del mes$ 0,00');
  await bank.locator('summary').click();
  await expect(bank).toContainText('Transferencias recibidas');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('account-summary.png'), fullPage: true });
});


test('dashboard counts account openings in their month and preserves available balance', async ({ page }) => {
  await isolateHousehold(page, 'Dashboard aperturas');
  const { csrfToken } = await (await page.request.get('/api/v1/auth/csrf/')).json();
  const headers = { 'X-CSRFToken': csrfToken };
  const created = [];
  for (const [name, amount] of [['Sueldo', '1798000.00'], ['Gremio Judiciales', '345000.00']]) {
    const response = await page.request.post('/api/v1/accounts/', {
      headers: { ...headers, 'Idempotency-Key': crypto.randomUUID() },
      data: { name, kind: 'bank', opening_balance: amount, opening_date: '2026-10-10' },
    });
    expect(response.status()).toBe(201);
    created.push(await response.json());
  }
  const categories = await (await page.request.get('/api/v1/categories/')).json();
  const expenseCategory = categories.results.find((category: { type: string }) => category.type === 'expense');
  const expense = await page.request.post('/api/v1/transactions/', {
    headers: { ...headers, 'Idempotency-Key': crypto.randomUUID() },
    data: { type: 'expense', account_id: created[0].id, category_id: expenseCategory.id, amount: '45000.00', effective_date: '2026-10-11' },
  });
  expect(expense.status()).toBe(201);
  await page.goto('/app');
  await page.getByLabel('Mes', { exact: true }).fill('2026-10');
  await expect(page.getByTestId('monthly-income').locator('.kpi-amount')).toContainText('2.143.000,00');
  await expect(page.getByTestId('account-income').filter({ hasText: 'Sueldo' })).toContainText('1.798.000,00');
  await expect(page.getByTestId('account-income').filter({ hasText: 'Gremio Judiciales' })).toContainText('345.000,00');
  await expect(page.getByTestId('monthly-expense')).toContainText('45.000,00');
  await expect(page.getByTestId('available-balance')).toContainText('2.098.000,00');
  await page.getByRole('button', { name: 'Mes siguiente' }).click();
  await expect(page.getByTestId('monthly-income').locator('.kpi-amount')).toContainText('0,00');
  await expect(page.getByTestId('available-balance')).toContainText('2.098.000,00');
});
