import { test, expect } from '@playwright/test';
import metadata from '../src/generated/metadata.json' with { type: 'json' };
import saved from '../src/generated/saved-overview.json' with { type: 'json' };

test.beforeEach(async ({ context }) => {
  await context.route('**/api/v1/fda/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/metadata') || path.endsWith('/explore')) {
      await route.fulfill({ json: path.endsWith('/metadata') ? metadata : saved });
    } else {
      await route.fulfill({ status: 503, json: { error: { code: 'SERVICE_BUSY', message: 'Controlled theme fixture.', details: [], retryable: true }, requestId: 'theme-fixture' } });
    }
  });
});

test('home link and theme preserve the current view without another query', async ({ page }) => {
  const requests: string[] = [];
  page.on('request', request => { if (request.url().includes('/api/v1/fda/')) requests.push(request.url()); });
  await page.goto('/');
  await expect(page.getByTestId('overview-section')).toHaveAttribute('data-state', 'success');
  const home = page.getByRole('link', { name: 'Project Lab: back to portfolio' });
  await expect(home).toHaveAttribute('href', 'https://abdul-rahmansayed.github.io/');
  await expect(home).not.toHaveAttribute('target');
  const url = page.url();
  const count = requests.length;
  const metrics = await page.locator('.metrics').innerText();
  await page.getByRole('button', { name: 'Switch to light mode' }).click();
  await expect(page.locator('html')).not.toHaveClass(/dark/);
  expect(await page.evaluate(() => localStorage.getItem('theme'))).toBe('light');
  expect(page.url()).toBe(url);
  expect(await page.locator('.metrics').innerText()).toBe(metrics);
  expect(requests).toHaveLength(count);
  await page.reload();
  await expect(page.getByRole('button', { name: 'Switch to dark mode' })).toBeVisible();
  await page.getByRole('tab', { name: 'Reports', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Matching reports', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Switch to dark mode' }).click();
  await expect(page.getByRole('tab', { name: 'Reports', exact: true })).toHaveAttribute('aria-selected', 'true');
  await page.getByRole('tab', { name: 'Snapshot & methods', exact: true }).click();
  await page.getByRole('button', { name: 'Switch to light mode' }).click();
  await expect(page.getByRole('heading', { name: 'Snapshot & methods', exact: true })).toBeVisible();
});

test('the saved preference and later changes synchronize across tabs', async ({ page, context }) => {
  await page.goto('/');
  const other = await context.newPage();
  await other.goto('/');
  await page.getByRole('button', { name: 'Switch to light mode' }).click();
  await expect(other.getByRole('button', { name: 'Switch to dark mode' })).toBeVisible();
  await other.getByRole('button', { name: 'Switch to dark mode' }).click();
  await expect(page.getByRole('button', { name: 'Switch to light mode' })).toBeVisible();
  await page.evaluate(() => localStorage.clear());
  await expect(other.locator('html')).toHaveClass(/dark/);
});

test('blocked browser storage leaves the theme control usable', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => {
    for (const method of ['getItem', 'setItem']) Object.defineProperty(Storage.prototype, method, { value() { throw new DOMException('Storage blocked', 'SecurityError'); } });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Switch to light mode' }).click();
  await expect(page.getByRole('button', { name: 'Switch to dark mode' })).toBeVisible();
  await page.getByRole('button', { name: 'Switch to dark mode' }).click();
  await expect(page.locator('html')).toHaveClass(/dark/);
  expect(errors).toEqual([]);
});

for (const theme of ['dark', 'light']) test(`${theme} controls and chart colors remain readable at mobile width`, async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 844 });
  await page.addInitScript(value => localStorage.setItem('theme', value), theme);
  await page.goto('/');
  await expect(page.getByTestId('overview-section')).toHaveAttribute('data-state', 'success');
  const colors = await page.evaluate(() => {
    const sample = document.createElement('span');
    document.body.append(sample);
    const color = (name: string) => { sample.style.color = `var(--${name})`; return getComputedStyle(sample).color; };
    const luminance = (value: string) => value.match(/[\d.]+/g)!.slice(0, 3).map(Number).reduce((sum, channel, index) => {
      const s = channel / 255;
      return sum + (s <= .04045 ? s / 12.92 : ((s + .055) / 1.055) ** 2.4) * [.2126, .7152, .0722][index];
    }, 0);
    const ratio = (a: string, b: string) => {
      const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
      return (values[0] + .05) / (values[1] + .05);
    };
    const result = {
      text: ['ink', 'muted', 'link', 'success', 'error'].map(name => ratio(color(name), color('page'))),
      notices: [ratio(color('info-ink'), color('info-bg')), ratio(color('warning-ink'), color('warning-bg'))],
      marks: ['teal', 'coral', 'products', 'outcomes', 'reactions', 'partial'].map(name => ratio(color(name), color('page'))),
      border: ratio(color('control-border'), color('surface')),
      overflow: document.documentElement.scrollWidth > innerWidth,
    };
    sample.remove();
    return result;
  });
  for (const value of [...colors.text, ...colors.notices]) expect(value).toBeGreaterThanOrEqual(4.5);
  for (const value of [...colors.marks, colors.border]) expect(value).toBeGreaterThanOrEqual(3);
  expect(colors.overflow).toBe(false);
  await page.getByRole('button', { name: 'Show table for annual reports' }).click();
  await expect(page.getByRole('region', { name: 'Annual reports values' })).toBeVisible();
  await expect(page.getByRole('button', { name: `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode` })).toBeVisible();
});
