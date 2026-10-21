import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e-deployment',
  timeout: 45000,
  expect: { timeout: 12000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  outputDir: '../generated/deployment/playwright',
  reporter: [['list'], ['json', { outputFile: '../generated/deployment/browser-results.json' }]],
  use: {
    baseURL: 'https://127.0.0.1:4174/Project-Lab/', channel: 'chrome',
    viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce',
    // Only this isolated loopback suite trusts the temporary self-signed certificate.
    ignoreHTTPSErrors: true, trace: 'retain-on-failure', screenshot: 'only-on-failure',
  },
});
