import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e', workers: 1, fullyParallel: false, retries: 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: 'http://127.0.0.1:4201', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1280, height: 800 }, storageState: 'e2e/.auth/desktop.json' } },
    { name: 'mobile360', use: { viewport: { width: 360, height: 740 }, isMobile: true, hasTouch: true, storageState: 'e2e/.auth/mobile360.json' } },
    { name: 'mobile390', use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, storageState: 'e2e/.auth/mobile390.json' } },
  ],
  webServer: [
    { command: '../.venv/bin/python ../backend/tests/e2e_server.py', url: 'http://127.0.0.1:8001/api/v1/health/', reuseExistingServer: false, gracefulShutdown: { signal: 'SIGTERM', timeout: 10000 }, timeout: 120000 },
    { command: 'npx ng serve --host 127.0.0.1 --port 4201 --proxy-config proxy.e2e.json', url: 'http://127.0.0.1:4201', reuseExistingServer: false, gracefulShutdown: { signal: 'SIGTERM', timeout: 10000 }, timeout: 120000 },
  ],
});
