import { expect, Page } from '@playwright/test';

// All E2E requests target the disposable database created by e2e_server.py.
export async function isolateHousehold(page: Page, name: string): Promise<void> {
  const csrf = await page.request.get('/api/v1/auth/csrf/');
  const { csrfToken } = await csrf.json();
  const response = await page.request.post('/api/v1/households/', { data: { name }, headers: { 'X-CSRFToken': csrfToken } });
  expect(response.status()).toBe(201);
}
