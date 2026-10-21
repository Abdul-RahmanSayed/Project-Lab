import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 45000,
  expect: { timeout: 10000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  outputDir: '../generated/frontend/playwright',
  reporter: [['list'], ['json', { outputFile: '../generated/frontend/e2e-results.json' }]],
  use: { baseURL: process.env.FRONTEND_URL ?? 'http://127.0.0.1:4173', channel: 'chrome',
    viewport: { width: 1440, height: 1000 }, locale: 'en-US', timezoneId: 'America/New_York',
    reducedMotion: 'reduce', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
});
