import { test, expect } from '@playwright/test';
import type { Page, Route } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import saved from '../src/generated/saved-overview.json' with { type: 'json' };
import metadata from '../src/generated/metadata.json' with { type: 'json' };
import type { OverviewResponse } from '../src/types';

const imageDirectory = '../generated/frontend/screenshots';
const errors = new WeakMap<Page, string[]>();
test.beforeEach(async ({ page }) => {
  const failures: string[] = [];
  errors.set(page, failures);
  page.on('pageerror', error => failures.push(error.message));
});
test.afterEach(async ({ page }) => expect(errors.get(page)).toEqual([]));

async function ready(page: Page) {
  await expect(page.locator('.api-status')).toHaveText('API ready');
  await expect(page.getByTestId('overview-section')).toHaveAttribute('data-state', 'success');
  await page.evaluate(() => document.fonts.ready.then(() => undefined));
}
async function apply(page: Page, product: string, start = '2002', end = '2026') {
  const toggle = page.getByRole('button', { name: 'Filters', exact: true });
  if (await toggle.isVisible() && await toggle.getAttribute('aria-expanded') === 'false') await toggle.click();
  await page.getByLabel('Start year').selectOption(start);
  await page.getByLabel('End year').selectOption(end);
  await page.getByLabel('Raw suspect-product name').fill(product);
  await page.getByRole('button', { name: 'Apply', exact: true }).click();
}
async function fulfill(route: Route, value: unknown, status = 200) {
  await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(value) });
}
function failure(code: string, retryable = true) {
  return { error: { code, message: 'Controlled test response.', details: [], retryable }, requestId: 'browser-fixture' };
}
function fixture(product: string, count: number) {
  const value = structuredClone(saved) as OverviewResponse;
  value.source = 'sqlite';
  value.label = 'Queried overview / data snapshot';
  value.overview.appliedFilters.productFilter = product;
  value.overview.selectedCount = count;
  value.overview.validAgeCount = 0;
  value.overview.missingAgeCount = count;
  value.overview.ageMeans = { total: null, female: null, male: null };
  value.overview.yearCounts = value.overview.yearCounts.map(([year]) => [year, year === 2002 ? count : 0]);
  value.overview.ageHistogram = value.overview.ageHistogram.map(([bin]) => [bin, 0]);
  value.overview.genderCounts = [['Female', 0], ['Male', 0], ['Unknown', count]];
  value.overview.rankings = { products: [], outcomes: [], reactions: [] };
  return value;
}

test('portfolio styling: local fonts, readable semantic colors, tables and dialog', async ({ page }) => {
  await page.goto('/');
  await ready(page);
  const theme = await page.evaluate(() => {
    const root = getComputedStyle(document.documentElement);
    const rgb = (value: string) => value.match(/[\d.]+/g)!.slice(0, 3).map(Number);
    const luminance = (value: string) => rgb(value).reduce((sum, channel, index) => {
      const s = channel / 255;
      return sum + (s <= .04045 ? s / 12.92 : ((s + .055) / 1.055) ** 2.4) * [.2126, .7152, .0722][index];
    }, 0);
    const contrast = (foreground: string, background: string) => {
      const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
      return (values[0] + .05) / (values[1] + .05);
    };
    const token = (name: string) => {
      const sample = document.createElement('span');
      sample.style.color = `var(--${name})`;
      document.body.append(sample);
      const color = getComputedStyle(sample).color;
      sample.remove();
      return color;
    };
    const button = getComputedStyle(document.querySelector('.button.primary')!);
    return {
      scheme: root.colorScheme,
      page: root.backgroundColor,
      font: getComputedStyle(document.body).fontFamily,
      mono: getComputedStyle(document.querySelector('.metrics dd')!).fontFamily,
      fonts: [...document.fonts].filter(font => font.status === 'loaded').map(font => font.family),
      fontUrls: performance.getEntriesByType('resource').map(entry => entry.name).filter(url => url.endsWith('.woff2')),
      textContrast: ['ink', 'muted', 'link', 'success', 'error'].map(name => contrast(token(name), token('page'))),
      infoContrast: contrast(token('info-ink'), token('info-bg')),
      warningContrast: contrast(token('warning-ink'), token('warning-bg')),
      buttonContrast: contrast(button.color, button.backgroundColor),
      borderContrast: contrast(token('control-border'), token('surface')),
      markContrast: ['teal', 'coral', 'products', 'outcomes', 'reactions', 'partial'].map(name => contrast(token(name), token('page'))),
    };
  });
  expect(theme.scheme).toBe('dark');
  expect(theme.page).toBe('rgb(11, 11, 19)');
  expect(theme.font).toContain('Inter Variable');
  expect(theme.mono).toContain('JetBrains Mono Variable');
  expect(theme.fonts).toEqual(expect.arrayContaining(['Inter Variable', 'JetBrains Mono Variable']));
  expect(theme.fontUrls).toHaveLength(2);
  expect(theme.fontUrls.every(url => new URL(url).origin === new URL(page.url()).origin)).toBe(true);
  for (const value of [...theme.textContrast, theme.infoContrast, theme.warningContrast, theme.buttonContrast]) expect(value).toBeGreaterThanOrEqual(4.5);
  for (const value of [...theme.markContrast, theme.borderContrast]) expect(value).toBeGreaterThanOrEqual(3);
  await writeFile('../generated/frontend/theme-check.json', JSON.stringify(theme, null, 2));
  await mkdir(imageDirectory, { recursive: true });
  await page.getByRole('button', { name: 'Show table for annual reports', exact: true }).click();
  await page.screenshot({ path: `${imageDirectory}/portfolio-tables-1440.png` });
  await page.getByRole('tab', { name: 'Snapshot & methods' }).click();
  await page.screenshot({ path: `${imageDirectory}/portfolio-methods-1440.png`, fullPage: true });
  await page.getByRole('tab', { name: 'Reports', exact: true }).click();
  await expect(page.locator('.report-link').first()).toBeEnabled();
  await page.screenshot({ path: `${imageDirectory}/portfolio-reports-1440.png` });
  await page.locator('.report-link').first().click();
  await expect(page.getByRole('dialog').getByRole('heading', { name: 'Products in this report' })).toBeVisible();
  await page.screenshot({ path: `${imageDirectory}/portfolio-dialog-1440.png` });
});

test('real API: five plots, exact filtered counts, tables, and reset', async ({ page }) => {
  await page.goto('/');
  await ready(page);
  await expect(page.getByTestId('selected-count')).toHaveText('97,652');
  await expect(page.locator('[data-chart]')).toHaveCount(5);
  const maximum = Math.max(...Object.values(saved.overview.rankings).flatMap(rows => rows.map(row => Number(row[1]))));
  for (const field of ['products', 'outcomes', 'reactions'] as const) {
    const width = Number(await page.locator(`[data-chart="${field}"] .ranking-list rect`).first().getAttribute('width'));
    expect(width).toBeCloseTo(Number(saved.overview.rankings[field][0][1]) / maximum * 100, 8);
  }
  await expect(page.getByText('* 2026 covers January 1 only, not a full year.')).toBeVisible();
  await apply(page, 'CARROTS', '2024');
  await expect(page.getByTestId('selected-count')).toHaveText('149');
  await expect(page.getByTestId('overview-section')).toHaveAttribute('data-state', 'success');
  await expect(page.locator('.metrics')).toContainText('123');
  await page.getByRole('button', { name: 'Show table for annual reports', exact: true }).click();
  const annual = page.locator('[data-chart="annual"]');
  await expect(annual.locator('tbody tr')).toHaveCount(3);
  await expect(annual.locator('tbody tr').nth(0)).toContainText('122');
  await expect(annual.locator('tbody tr').nth(1)).toContainText('27');
  await expect(annual.locator('tbody tr').nth(2)).toContainText('January 1 only');
  await page.getByRole('button', { name: 'Show table for age distribution', exact: true }).click();
  await expect(page.locator('[data-chart="ages"] tbody tr')).toHaveCount(126);
  await expect(page.locator('[data-chart="ages"] tbody tr').last()).toContainText('Exactly 125');
  await page.getByRole('button', { name: 'Reset selection', exact: true }).click();
  await expect(page.getByTestId('selected-count')).toHaveText('97,652');
  await expect(page.getByTestId('overview-section')).toHaveAttribute('data-state', 'success');
});

test('real API: report pagination, page size, detail, Escape and focus return', async ({ page }) => {
  await page.goto('/');
  await ready(page);
  await apply(page, 'CARROTS', '2024');
  await expect(page.getByTestId('selected-count')).toHaveText('149');
  await page.getByRole('tab', { name: 'Reports', exact: true }).click();
  const rows = page.getByRole('region', { name: 'Matching report rows', exact: true });
  await expect(rows.locator('tbody tr')).toHaveCount(25);
  const firstId = await rows.locator('.report-link').first().innerText();
  await page.getByRole('button', { name: 'Next report page', exact: true }).click();
  await expect(page.locator('.pagination')).toContainText('Page 2');
  await expect(rows.locator('.report-link').first()).not.toHaveText(firstId);
  await page.getByRole('button', { name: 'Previous report page', exact: true }).click();
  await expect(rows.locator('.report-link').first()).toHaveText(firstId);
  const inspect = page.getByRole('button', { name: `View report ${firstId}`, exact: true });
  await inspect.click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('heading', { name: 'Products in this report' })).toBeVisible();
  await expect(dialog.getByText('Source position', { exact: true })).toBeVisible();
  await expect(dialog.locator('.provenance')).toContainText('.json');
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(inspect).toBeFocused();
  await page.getByLabel('Rows per page').selectOption('100');
  await expect(rows.locator('tbody tr')).toHaveCount(100);
  await expect(page.locator('.pagination')).toContainText('Page 1');
  await page.getByRole('button', { name: 'Next report page', exact: true }).click();
  await expect(rows.locator('tbody tr')).toHaveCount(49);
  await expect(page.getByRole('button', { name: 'Next report page', exact: true })).toBeDisabled();
});

test('real API: empty selection, literal punctuation, draft-only typing and raw transport', async ({ page }) => {
  const searches: string[] = [];
  page.on('request', request => { if (request.url().includes('/explore?')) searches.push(new URL(request.url()).searchParams.get('productFilter') ?? ''); });
  await page.goto('/');
  await ready(page);
  searches.length = 0;
  await page.getByLabel('Raw suspect-product name').fill('CARROTS');
  await page.waitForTimeout(150);
  expect(searches).toEqual([]);
  for (const [product, count] of [['%', '734'], ['_', '2'], ['+', '1,811'], ['no-match-7c46ba', '0']]) {
    await apply(page, product);
    await expect(page.getByTestId('selected-count')).toHaveText(count);
  }
  await expect(page.getByText('No reports match this selection.', { exact: true })).toBeVisible();
  await expect(page.locator('.mean-age')).toHaveText('Not available');
  expect(searches).toContain('+');
  await apply(page, '   ');
  await expect(page.getByRole('alert')).toContainText('nonblank');
  await expect(page.getByTestId('selected-count')).toHaveText('0');
});

test('all five aggregate tables agree exactly with the real API selection', async ({ page, request }) => {
  await page.goto('/');
  await ready(page);
  const response = await request.get('/api/v1/fda/explore?startYear=2024&endYear=2026&productFilter=CARROTS&releaseId=' + encodeURIComponent(metadata.releaseId));
  expect(response.ok()).toBe(true);
  const expected = (await response.json()).overview;
  await apply(page, 'CARROTS', '2024');
  await expect(page.getByTestId('selected-count')).toHaveText('149');
  for (const label of ['annual reports', 'age distribution', 'suspect products', 'outcomes', 'reactions']) {
    await page.getByRole('button', { name: `Show table for ${label}`, exact: true }).click();
  }
  const values = async (chart: string) => page.locator(`[data-chart="${chart}"] tbody tr`).evaluateAll(rows => rows.map(row => row.querySelector('td')!.textContent!.replaceAll(',', '')));
  expect(await values('annual')).toEqual(expected.yearCounts.map((row: [number, number]) => String(row[1])));
  expect(await values('ages')).toEqual(expected.ageHistogram.map((row: [number, number]) => String(row[1])));
  for (const field of ['products', 'outcomes', 'reactions']) {
    const rows = page.locator(`[data-chart="${field}"] tbody tr`);
    const names = await rows.locator('th').allTextContents();
    const expectedNames = expected.rankings[field].map(([term]: [string, number]) => field === 'products' ? metadata.metadata.termDisplayOverrides.find(item => item.canonical === term)?.displayLabel ?? term : term);
    expect(names).toEqual(expectedNames);
    expect(await values(field)).toEqual(expected.rankings[field].map((row: [string, number]) => String(row[1])));
  }
});

test('reset also clears unapplied text when the committed selection is already default', async ({ page }) => {
  await page.goto('/');
  await ready(page);
  await page.getByLabel('Raw suspect-product name').fill('unapplied text');
  await page.getByRole('button', { name: 'Reset selection', exact: true }).click();
  await expect(page.getByLabel('Raw suspect-product name')).toHaveValue('');
  await expect(page.getByText('Unapplied changes.', { exact: true })).toHaveCount(0);
  await expect(page.getByTestId('selected-count')).toHaveText('97,652');
});

test('real API: back/forward, reload, tab state and invalid URL repair', async ({ page }) => {
  await page.goto('/');
  await ready(page);
  await apply(page, 'CARROTS');
  await expect(page.getByTestId('selected-count')).toHaveText('241');
  await page.getByRole('tab', { name: 'Snapshot & methods' }).click();
  await page.reload();
  await expect(page.getByRole('tab', { name: 'Snapshot & methods' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByRole('heading', { name: 'Selection and counting' })).toBeVisible();
  await page.getByRole('tab', { name: 'Overview', exact: true }).click();
  await expect(page.getByTestId('selected-count')).toHaveText('241');
  await apply(page, 'VITAMIN D3');
  await expect(page.getByTestId('selected-count')).toHaveText('278');
  await page.goBack();
  await expect(page.getByTestId('selected-count')).toHaveText('241');
  await page.goForward();
  await expect(page.getByTestId('selected-count')).toHaveText('278');
  await page.goto('/#/fda?startYear=2026&endYear=2024');
  await expect(page.getByRole('alert')).toContainText('Invalid shared view');
  await expect(page.getByRole('button', { name: 'Apply', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Use saved default view', exact: true }).click();
  await ready(page);
  await expect(page.getByTestId('selected-count')).toHaveText('97,652');
});

test('delayed old response cannot overwrite a newer selection; old data keeps its label', async ({ page }) => {
  await page.addInitScript(({ heldResponse }) => {
    const realFetch = window.fetch.bind(window);
    // Deliberately ignore AbortSignal to exercise the generation guard itself.
    window.fetch = (...args) => {
      const input = args[0];
      const url = new URL(typeof input === 'string' ? input : input instanceof URL ? input.href : input.url, location.href);
      if (url.pathname.endsWith('/explore') && url.searchParams.get('productFilter') === 'CARROTS') {
        return new Promise<Response>(resolve => {
          (window as unknown as { releaseOldFixture: () => void }).releaseOldFixture = () => resolve(new Response(JSON.stringify(heldResponse), { headers: { 'Content-Type': 'application/json' } }));
        });
      }
      return realFetch(...args);
    };
  }, { heldResponse: fixture('CARROTS', 241) });
  await page.route('**/api/v1/fda/metadata?*', route => fulfill(route, metadata));
  await page.route('**/api/v1/fda/explore?*', async route => {
    const product = new URL(route.request().url()).searchParams.get('productFilter');
    await fulfill(route, product ? fixture(product, 278) : saved);
  });
  await page.goto('/');
  await ready(page);
  await apply(page, 'CARROTS');
  await expect(page.getByTestId('overview-section')).toHaveAttribute('data-state', 'loading');
  await expect(page.getByTestId('selected-count')).toHaveText('97,652');
  await expect(page.locator('.results-heading')).toContainText('All suspect products');
  await expect(page.locator('.result-origin')).toHaveText('Previous result');
  await apply(page, 'VITAMIN D3');
  await expect(page.getByTestId('selected-count')).toHaveText('278');
  await page.evaluate(() => (window as unknown as { releaseOldFixture: () => void }).releaseOldFixture());
  await page.waitForTimeout(150);
  await expect(page.getByTestId('selected-count')).toHaveText('278');
  await expect(page.locator('.results-heading')).toContainText('VITAMIN D3');
});

test('no-age and hostile raw labels render as data, without HTML execution', async ({ page }) => {
  const product = '<img src=x onerror=alert(1)>';
  let dialogs = 0;
  page.on('dialog', async dialog => { dialogs++; await dialog.dismiss(); });
  await page.route('**/api/v1/fda/metadata?*', route => fulfill(route, metadata));
  await page.route('**/api/v1/fda/explore?*', route => {
    const text = new URL(route.request().url()).searchParams.get('productFilter');
    return fulfill(route, text ? fixture(text, 12) : saved);
  });
  await page.goto('/');
  await ready(page);
  await apply(page, product);
  await expect(page.getByTestId('selected-count')).toHaveText('12');
  await expect(page.getByText('No valid ages in this selection. Mean age is not available.')).toBeVisible();
  await expect(page.locator('.mean-age')).toHaveText('Not available');
  await expect(page.locator('.results-heading code')).toHaveText(product);
  await expect(page.locator('img')).toHaveCount(0);
  expect(dialogs).toBe(0);
});

for (const code of ['SERVICE_BUSY', 'RATE_LIMITED', 'QUERY_TIMEOUT', 'RELEASE_MISMATCH']) {
  test(`query failure ${code} is explicit and never replaces previous numbers`, async ({ page }) => {
    let failedCalls = 0;
    await page.route('**/api/v1/fda/metadata?*', route => fulfill(route, metadata));
    await page.route('**/api/v1/fda/explore?*', route => {
      if (new URL(route.request().url()).searchParams.has('productFilter')) { failedCalls++; return fulfill(route, failure(code), code === 'RATE_LIMITED' ? 429 : code === 'RELEASE_MISMATCH' ? 409 : 503); }
      return fulfill(route, saved);
    });
    await page.goto('/');
    await ready(page);
    await apply(page, 'CARROTS');
    await expect(page.getByTestId('overview-section')).toHaveAttribute('data-state', 'error');
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByTestId('selected-count')).toHaveText('97,652');
    await expect(page.locator('.results-heading')).toContainText('All suspect products');
    await page.waitForTimeout(150);
    expect(failedCalls).toBe(1);
    await page.getByRole('button', { name: 'Retry overview', exact: true }).click();
    await expect.poll(() => failedCalls).toBe(2);
  });
}

test('a default payload for a filtered request is rejected, not relabeled', async ({ page }) => {
  await page.route('**/api/v1/fda/metadata?*', route => fulfill(route, metadata));
  await page.route('**/api/v1/fda/explore?*', route => fulfill(route, saved));
  await page.goto('/');
  await ready(page);
  await apply(page, 'CARROTS');
  await expect(page.getByRole('alert')).toContainText('No different snapshot or selection has been substituted');
  await expect(page.locator('.results-heading')).toContainText('All suspect products');
});

test('offline connection stops after three attempts; saved default remains usable', async ({ page }) => {
  let calls = 0;
  await page.route('**/api/v1/fda/metadata?*', route => { calls++; return fulfill(route, failure('DATA_UNAVAILABLE'), 503); });
  await page.goto('/');
  await expect(page.getByTestId('selected-count')).toHaveText('97,652');
  await expect(page.locator('.result-origin')).toHaveText('Saved overview / data snapshot');
  await expect(page.locator('.api-status')).toHaveText('API unavailable');
  await mkdir(imageDirectory, { recursive: true });
  await page.screenshot({ path: `${imageDirectory}/portfolio-unavailable-1440.png` });
  const completed = calls;
  expect(completed).toBeGreaterThanOrEqual(3);
  expect(completed).toBeLessThanOrEqual(4); // Development StrictMode may abort an initial attempt.
  await page.waitForTimeout(250);
  expect(calls).toBe(completed);
  await expect(page.getByRole('button', { name: 'Apply', exact: true })).toBeDisabled();
  await page.getByRole('tab', { name: 'Reports', exact: true }).click();
  await expect(page.getByText('Report queries are unavailable until the API is ready.', { exact: false })).toBeVisible();
});

test('a custom shared view never receives the unrelated default during an outage', async ({ page }) => {
  await page.route('**/api/v1/fda/metadata?*', route => fulfill(route, failure('RELEASE_MISMATCH', false), 409));
  await page.goto('/#/fda?productFilter=CARROTS');
  await expect(page.locator('.api-status')).toHaveText('API unavailable');
  await expect(page.getByTestId('selected-count')).toHaveCount(0);
  await expect(page.getByRole('alert')).toContainText('does not match');
});

test('keyboard navigation, skip link and source identities', async ({ page }) => {
  await page.goto('/');
  await ready(page);
  const hash = new URL(page.url()).hash;
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to FDA Explorer' })).toBeFocused();
  await page.keyboard.press('Enter');
  expect(new URL(page.url()).hash).toBe(hash);
  await expect(page.getByRole('main')).toBeFocused();
  await page.getByRole('tab', { name: 'Overview', exact: true }).focus();
  await page.keyboard.press('End');
  await expect(page.getByRole('tab', { name: 'Snapshot & methods' })).toBeFocused();
  await page.getByText('Release and policy identities', { exact: true }).click();
  await expect(page.locator('.identifiers')).toContainText(metadata.releaseId);
});

test('copy link preserves the committed exact selection and tab', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('/');
  await ready(page);
  await apply(page, ' + ');
  await expect(page.getByTestId('overview-section')).toHaveAttribute('data-state', 'success');
  await page.getByRole('tab', { name: 'Snapshot & methods' }).click();
  await page.getByRole('button', { name: 'Copy view link', exact: true }).click();
  await expect(page.getByRole('status').filter({ hasText: 'View link copied.' })).toHaveText('View link copied.');
  const link = await page.evaluate(() => navigator.clipboard.readText());
  expect(link).toBe(page.url());
  const params = new URLSearchParams(new URL(link).hash.slice(6));
  expect(params.get('productFilter')).toBe(' + ');
  expect(params.get('tab')).toBe('source');
  expect(params.get('releaseId')).toBe(metadata.releaseId);
});

test('touch controls apply a selection and open and close report details', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, reducedMotion: 'reduce' });
  const page = await context.newPage();
  try {
    await page.goto(process.env.FRONTEND_URL ?? 'http://127.0.0.1:4173/');
    await ready(page);
    await page.getByRole('button', { name: 'Filters', exact: true }).tap();
    await page.getByLabel('Start year').selectOption('2024');
    await page.getByLabel('Raw suspect-product name').fill('CARROTS');
    await page.getByRole('button', { name: 'Apply', exact: true }).tap();
    await expect(page.getByTestId('selected-count')).toHaveText('149');
    await page.getByRole('tab', { name: 'Reports', exact: true }).tap();
    await expect(page.locator('.report-link').first()).toBeEnabled();
    await page.locator('.report-link').first().tap();
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('dialog').getByRole('heading', { name: 'Products in this report' })).toBeVisible();
    await mkdir(imageDirectory, { recursive: true });
    await page.screenshot({ path: `${imageDirectory}/portfolio-dialog-390.png` });
    await page.getByRole('button', { name: 'Close report details', exact: true }).tap();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  } finally { await context.close(); }
});

for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }, { width: 320, height: 740 }]) {
  test(`real rendered layout ${viewport.width}px: visible marks, no body overflow, screenshots`, async ({ page, browser }) => {
    await page.setViewportSize(viewport);
    await page.goto('/');
    await ready(page);
    await expect(page.locator('[data-chart="annual"] .data-mark')).toHaveCount(25);
    await expect(page.locator('[data-chart="ages"] .data-mark')).toHaveCount(126);
    const layout = await page.evaluate(() => ({
      bodyWidth: document.documentElement.scrollWidth, viewport: innerWidth,
      nonzero: [...document.querySelectorAll('[data-chart="annual"] .data-mark')].filter(mark => Number(mark.getAttribute('height')) > 0).length,
      plots: [...document.querySelectorAll('[data-chart]')].map(plot => ({ left: plot.getBoundingClientRect().left, right: plot.getBoundingClientRect().right })),
    }));
    expect(layout.bodyWidth).toBeLessThanOrEqual(layout.viewport + 1);
    expect(layout.nonzero).toBeGreaterThan(0);
    expect(layout.plots.every(plot => plot.left >= 0 && plot.right <= layout.viewport + 1)).toBe(true);
    await mkdir(imageDirectory, { recursive: true });
    const diagnostics = await page.evaluate(() => ({
      renderReadyMs: performance.now(),
      domNodes: document.querySelectorAll('*').length,
      dataMarks: document.querySelectorAll('.data-mark').length,
      usedJsHeapBytes: (performance as unknown as { memory?: { usedJSHeapSize: number } }).memory?.usedJSHeapSize ?? null,
      bodyWidth: document.documentElement.scrollWidth,
      viewportWidth: innerWidth,
    }));
    await writeFile(`../generated/frontend/browser-${viewport.width}.json`, JSON.stringify({ ...diagnostics, browser: browser.version(), note: 'One local warm-API navigation, not p95, host performance, process RSS or a physical mobile device. Chromium heap values are diagnostic only.' }, null, 2));
    await page.screenshot({ path: `${imageDirectory}/default-${viewport.width}.png`, fullPage: true });
    await page.screenshot({ path: `${imageDirectory}/viewport-${viewport.width}.png` });
    if (viewport.width < 681) {
      await apply(page, 'CARROTS', '2024');
      await expect(page.getByTestId('selected-count')).toHaveText('149');
      await expect(page.getByRole('button', { name: 'Filters', exact: true })).toHaveAttribute('aria-expanded', 'false');
      await expect(page.getByRole('heading', { name: 'Displayed selection' })).toBeFocused();
      await page.screenshot({ path: `${imageDirectory}/filtered-${viewport.width}.png`, fullPage: true });
    }
    await page.setViewportSize({ width: 960, height: 720 });
    await expect(page.locator('[data-chart="annual"] .plot-body > svg')).toHaveCount(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  });
}
