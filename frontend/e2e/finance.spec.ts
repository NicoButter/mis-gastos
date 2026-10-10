import { test, expect, Page } from '@playwright/test';

async function navigate(page: Page, label: string) {
  const menu = page.getByRole('button', { name: 'Menú', exact: true });
  if (await menu.isVisible()) await menu.click();
  await page.getByRole('navigation', { name: 'Aplicación', exact: true }).getByRole('link', { name: label, exact: true }).click();
  if (await menu.isVisible()) await expect(page.getByRole('navigation', { name: 'Aplicación', exact: true })).toBeHidden();
}
async function createAccount(page: Page, name: string, opening: string) {
  await page.getByRole('button', { name: 'Agregar cuenta' }).click();
  await page.getByLabel('Nombre', { exact: true }).fill(name);
  await page.getByLabel('Saldo inicial').fill(opening);
  await page.getByRole('button', { name: 'Guardar cuenta', exact: true }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Cuenta guardada' })).toBeVisible();
  await expect(page.locator('article').filter({ has: page.getByRole('heading', { name, exact: true }) })).toBeVisible();
}
async function operation(page: Page, type: string, amount: string, description: string) {
  await page.getByRole('button', { name: 'Registrar movimiento' }).click();
  await page.getByRole('combobox', { name: 'Operación', exact: true }).selectOption(type);
  await page.getByLabel('Importe · ARS').fill(amount);
  if (type !== 'transfer') await page.locator('fieldset button[aria-pressed]').first().click();
  await page.getByRole('combobox', { name: type === 'income' ? 'Cuenta de destino' : 'Cuenta de origen', exact: true }).selectOption({ label: 'Efectivo E2E' });
  if (type === 'transfer') await page.getByRole('combobox', { name: 'Cuenta de destino', exact: true }).selectOption({ label: 'Banco E2E' });
  await page.getByLabel('Descripción opcional').fill(description);
  await page.getByRole('button', { name: type === 'expense' ? 'Guardar gasto' : type === 'income' ? 'Guardar ingreso' : 'Guardar transferencia', exact: true }).click();
  await expect(page.getByRole('heading', { name: description, exact: true })).toBeVisible();
}

test('sesión real, estados vacíos y ciclo financiero completo', async ({ page }, testInfo) => {
  await page.route('**/*google*/**', route => route.abort());
  await page.route('**/api/v1/auth/me/', async route => { await new Promise(resolve => setTimeout(resolve, 200)); await route.continue(); });
  await page.goto('/app');
  await expect(page.getByRole('heading', { name: 'Panel financiero' })).toBeVisible();
  await expect(page.getByText('Todavía no hay cuentas.', { exact: true })).toBeVisible();
  await navigate(page, 'Modo rápido');
  await expect(page.getByText('Necesitás una cuenta activa.', { exact: false })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Guardar gasto' })).toBeDisabled();
  await navigate(page, 'Cuentas');
  await createAccount(page, 'Efectivo E2E', '100,00');
  await createAccount(page, 'Banco E2E', '0');
  await navigate(page, 'Movimientos');
  await operation(page, 'income', '50', 'Ingreso E2E');
  await operation(page, 'expense', '10', 'Gasto E2E');
  await operation(page, 'transfer', '20', 'Transferencia E2E');
  const expense = page.locator('article').filter({ has: page.getByRole('heading', { name: 'Gasto E2E', exact: true }) });
  await expense.getByRole('button', { name: 'Corregir' }).click();
  await page.getByLabel('Importe · ARS').fill('15');
  await page.getByRole('button', { name: 'Guardar corrección' }).click();
  await expect(expense).toContainText('15,00');
  page.once('dialog', dialog => dialog.accept());
  await expense.getByRole('button', { name: 'Anular', exact: true }).click();
  await expect(expense).toContainText('Anulado');
  await expense.getByRole('button', { name: 'Historial' }).click();
  await expect(page.getByText('transaction.void', { exact: false })).toBeVisible();
  await navigate(page, 'Panel');
  await expect(page.locator('article').filter({ hasText: 'Saldo consolidado actual' })).toContainText('150,00');
  await navigate(page, 'Cuentas');
  await expect(page.locator('article').filter({ has: page.getByRole('heading', { name: 'Efectivo E2E', exact: true }) })).toContainText('130,00');
  await expect(page.locator('article').filter({ has: page.getByRole('heading', { name: 'Banco E2E', exact: true }) })).toContainText('20,00');
  await navigate(page, 'Modo rápido');
  await expect(page.getByLabel('Importe · ARS')).toHaveAttribute('inputmode', 'decimal');
  await page.getByLabel('Importe · ARS').fill('0');
  await expect(page.getByRole('button', { name: 'Guardar gasto' })).toBeDisabled();
  await page.getByLabel('Importe · ARS').fill('5,25');
  await page.locator('fieldset button[aria-pressed]').first().click();
  await page.getByLabel('Cuenta de origen').selectOption({ label: 'Efectivo E2E' });
  await page.getByRole('button', { name: 'Guardar gasto' }).click();
  await expect(page.getByRole('status')).toContainText('Movimiento guardado');
  await expect(page.getByLabel('Importe · ARS')).toHaveValue('');
  const keys: string[] = [];
  let releaseRetry!: () => void;
  const retryReleased = new Promise<void>(resolve => { releaseRetry = resolve; });
  await page.route('**/api/v1/transactions/', async route => {
    if (route.request().method() !== 'POST') { await route.continue(); return; }
    keys.push(route.request().headers()['idempotency-key']);
    if (keys.length === 1) { await route.fetch(); await route.abort(); }
    else { await retryReleased; await route.continue(); }
  });
  await page.getByLabel('Importe · ARS').fill('3');
  await page.getByRole('button', { name: 'Guardar gasto' }).click();
  await expect(page.getByRole('alert')).toContainText('reintentá');
  await page.getByRole('button', { name: 'Guardar gasto' }).click();
  await expect(page.getByLabel('Importe · ARS')).toBeDisabled();
  await page.getByRole('button', { name: 'Guardando…' }).evaluate(button => (button as HTMLButtonElement).click());
  releaseRetry();
  await expect(page.getByLabel('Importe · ARS')).toHaveValue('');
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBe(keys[1]);
  const summary = await page.request.get('/api/v1/dashboard/summary/');
  expect((await summary.json()).balance).toBe('141.75');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('quick.png'), fullPage: true });
  await navigate(page, 'Categorías');
  await expect(page.getByRole('heading', { name: 'Categorías', exact: true })).toBeVisible();
  await page.route('**/api/v1/dashboard/summary/**', route => route.fulfill({ status: 500, contentType: 'application/json', body: '{}' }));
  await navigate(page, 'Panel');
  await expect(page.getByRole('alert')).toContainText('reintentá');
});

test('visitante protegido sin autenticación alternativa', async ({ browser }) => {
  const context = await browser.newContext({ storageState: { cookies: [], origins: [] } });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:4201/app/quick');
  await expect(page).toHaveURL(/\/login/);
  await context.close();
});
