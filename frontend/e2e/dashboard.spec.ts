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
  await page.goto('/app');
  await page.getByLabel('Mes', { exact: true }).fill('2026-10');
  await expect(page.getByTestId('available-balance')).toContainText('170,30');
  await expect(page.getByTestId('monthly-income')).toContainText('120,10');
  await expect(page.getByTestId('monthly-expense')).toContainText('50,05');
  await expect(page.getByTestId('monthly-net')).toContainText('70,05');
  await expect(page.getByRole('progressbar', { name: 'Gastos frente a ingresos' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const balanceRows = page.locator('.account-balance-row');
  await expect(balanceRows).toHaveCount(2);
  await expect(balanceRows.first()).toHaveCSS('display', 'flex');
  const firstRow = await balanceRows.first().boundingBox();
  const secondRow = await balanceRows.last().boundingBox();
  expect(secondRow!.y).toBeGreaterThanOrEqual(firstRow!.y + firstRow!.height);
  await page.screenshot({ path: testInfo.outputPath('dashboard.png'), fullPage: true });
  await page.getByRole('button', { name: 'Mes anterior' }).click();
  await expect(page.getByLabel('Mes', { exact: true })).toHaveValue('2026-09');
  await expect(page.getByTestId('monthly-income')).toContainText('0,00');
  await expect(page.getByTestId('monthly-expense')).toContainText('0,00');
  await expect(page.getByTestId('available-balance')).toContainText('170,30');
  await expect(page.getByText('Sin ingresos positivos en este período para comparar los gastos.')).toBeVisible();
  await page.getByRole('button', { name: 'Mes siguiente' }).click();
  await expect(page.getByTestId('monthly-income')).toContainText('120,10');
  await page.getByRole('link', { name: 'Ver mis cuentas' }).click();
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
