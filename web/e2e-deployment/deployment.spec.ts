import { test, expect, request } from '@playwright/test';
import type { APIRequestContext, Page } from '@playwright/test';
import { spawn } from 'node:child_process';
import type { ChildProcess } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createServer } from 'node:net';
import lock from '../../deployment/release.lock.json' with { type: 'json' };

const root = resolve('..');
const python = resolve(root, process.platform === 'win32' ? '.venv-api/Scripts/python.exe' : '.venv-api/bin/python');
const directory = resolve(root, 'generated/deployment');
const origin = 'https://127.0.0.1:4174';
const apiOrigin = 'https://127.0.0.1:8767';
const cert = resolve(directory, 'tls/cert.pem'), key = resolve(directory, 'tls/key.pem');
let api: ChildProcess | undefined, preview: ChildProcess | undefined, http: APIRequestContext;
let logs = '';

test.describe.configure({ mode: 'serial' });

function launch(args: string[], environment: NodeJS.ProcessEnv = {}) {
  const command = args[0] === 'deployment.serve'
    ? ['-I', '-B', '-c', 'import sys; sys.path.insert(0, sys.argv.pop(1)); from deployment.serve import main; main()', resolve(directory, 'installed'), ...args.slice(1)]
    : ['-B', '-m', ...args];
  const child = spawn(python, command, { cwd: root, windowsHide: true,
    env: { ...process.env, ...environment }, stdio: ['ignore', 'pipe', 'pipe'] });
  child.on('error', error => { logs += error.message + '\n'; });
  for (const stream of [child.stdout, child.stderr]) stream?.on('data', chunk => { logs = (logs + chunk.toString()).slice(-32000); });
  return child;
}

async function unusedPort(port: number) {
  await new Promise<void>((resolve, reject) => {
    const probe = createServer();
    probe.once('error', () => reject(new Error(`Local test port ${port} is occupied; no existing process was stopped.`)));
    probe.listen(port, '127.0.0.1', () => probe.close(() => resolve()));
  });
}

async function stop(child: ChildProcess | undefined) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return;
  await new Promise<void>(resolve => { child.once('close', () => resolve()); child.kill(); });
}

async function startApi() {
  api = launch(['deployment.serve', '--lock', 'deployment/release.lock.json', '--host', '127.0.0.1',
    '--ssl-certfile', cert, '--ssl-keyfile', key], {
    FDA_RELEASE_DIRECTORY: resolve(directory, 'unpacked'), FDA_RELEASE_ID: lock.releaseId,
    FDA_ALLOWED_ORIGINS: origin, PORT: '8767',
  });
  await expect.poll(async () => {
    if (api?.exitCode !== null) throw new Error('Owned local API exited during startup: ' + logs);
    return http.get(apiOrigin + '/readyz').then(response => response.status()).catch(() => 0);
  }, { timeout: 20000, intervals: [100, 200, 500] }).toBe(200);
}

async function ready(page: Page) {
  await expect(page.locator('.api-status')).toHaveText('API ready');
  await expect(page.getByTestId('overview-section')).toHaveAttribute('data-state', 'success');
}

test.beforeAll(async () => {
  http = await request.newContext({ ignoreHTTPSErrors: true, timeout: 3000 });
  await mkdir(resolve(directory, 'screenshots'), { recursive: true });
  await unusedPort(4174);
  await unusedPort(8767);
  preview = launch(['deployment.preview', '--directory', resolve(directory, 'site'), '--port', '4174', '--certfile', cert, '--keyfile', key]);
  await expect.poll(() => {
    if (preview?.exitCode !== null) throw new Error('Owned static preview exited during startup: ' + logs);
    return http.get(origin + '/Project-Lab/').then(response => response.status()).catch(() => 0);
  }, { timeout: 15000 }).toBe(200);
  await startApi();
});

test.afterAll(async () => {
  await stop(api);
  await stop(preview);
  await http?.dispose();
  await writeFile(resolve(directory, 'local-https-server.log'), logs);
});

test('project-path build calls the separate HTTPS API and preserves reports and raw search', async ({ page }) => {
  const requests: string[] = [];
  page.on('request', request => { if (request.url().includes('/api/')) requests.push(request.url()); });
  await page.goto('./');
  await ready(page);
  await expect(page.getByTestId('selected-count')).toHaveText('97,652');
  await expect(page.locator('[data-chart]')).toHaveCount(5);
  await page.getByLabel('Start year').selectOption('2024');
  await page.getByLabel('Raw suspect-product name').fill('CARROTS');
  await page.getByRole('button', { name: 'Apply', exact: true }).click();
  await expect(page.getByTestId('selected-count')).toHaveText('149');
  await page.getByRole('tab', { name: 'Reports', exact: true }).click();
  await expect(page.locator('.report-link')).toHaveCount(25);
  await page.locator('.report-link').first().click();
  await expect(page.getByRole('dialog').getByRole('heading', { name: 'Products in this report' })).toBeVisible();
  await page.getByRole('button', { name: 'Close report details', exact: true }).click();
  await page.getByRole('tab', { name: 'Overview', exact: true }).click();
  await page.getByLabel('Start year').selectOption('2002');
  await page.getByLabel('Raw suspect-product name').fill('+');
  await page.getByRole('button', { name: 'Apply', exact: true }).click();
  await expect(page.getByTestId('selected-count')).toHaveText('1,811');
  await page.reload();
  await ready(page);
  await expect(page.getByTestId('selected-count')).toHaveText('1,811');
  expect(new URL(page.url()).pathname).toBe('/Project-Lab/');
  expect(requests.length).toBeGreaterThan(5);
  expect(requests.every(url => new URL(url).origin === apiOrigin)).toBe(true);
  expect(requests.some(url => new URL(url).searchParams.get('productFilter') === '+')).toBe(true);
  await page.screenshot({ path: resolve(directory, 'screenshots/cross-origin.png') });
});

test('real CORS headers expose a version error; a different browser origin cannot read the API', async ({ page }) => {
  const wrong = await http.get(apiOrigin + '/api/v1/fda/explore?releaseId=fda-release-sha256:' + '0'.repeat(64), { headers: { Origin: origin } });
  expect(wrong.status()).toBe(409);
  expect(wrong.headers()['access-control-allow-origin']).toBe(origin);
  expect((await wrong.json()).error.code).toBe('RELEASE_MISMATCH');
  const denied = await http.get(apiOrigin + '/api/v1/fda/metadata', { headers: { Origin: 'https://localhost:4174' } });
  expect(denied.status()).toBe(200); // CORS is a browser restriction, not authentication.
  expect(denied.headers()['access-control-allow-origin']).toBeUndefined();
  await page.goto('https://localhost:4174/Project-Lab/');
  await expect(page.locator('.api-status')).toHaveText('API unavailable');
  await expect(page.getByTestId('selected-count')).toHaveText('97,652');
  await expect(page.getByRole('button', { name: 'Apply', exact: true })).toBeDisabled();
});

test('real stopped API retains the saved default and manual Retry recovers after restart', async ({ page }) => {
  await page.goto('./');
  await ready(page);
  await stop(api);
  await page.reload();
  await expect(page.getByTestId('selected-count')).toHaveText('97,652');
  await expect(page.locator('.api-status')).toHaveText('API unavailable');
  await expect(page.locator('.result-origin')).toHaveText('Saved overview / data snapshot');
  await expect(page.getByRole('button', { name: 'Apply', exact: true })).toBeDisabled();
  await page.screenshot({ path: resolve(directory, 'screenshots/real-outage.png') });
  await startApi();
  await page.getByRole('button', { name: 'Retry API connection', exact: true }).click();
  await ready(page);
  await page.getByLabel('Start year').selectOption('2024');
  await page.getByLabel('Raw suspect-product name').fill('CARROTS');
  await page.getByRole('button', { name: 'Apply', exact: true }).click();
  await expect(page.getByTestId('selected-count')).toHaveText('149');
});

test('a custom shared selection gets no default during an actual outage and recovers its own result', async ({ page }) => {
  await stop(api);
  await page.goto('./#/fda?productFilter=CARROTS');
  await expect(page.locator('.api-status')).toHaveText('API unavailable');
  await expect(page.getByTestId('selected-count')).toHaveCount(0);
  await expect(page.locator('.results-heading')).toContainText('CARROTS');
  await startApi();
  await page.getByRole('button', { name: 'Retry API connection', exact: true }).click();
  await ready(page);
  await expect(page.getByTestId('selected-count')).toHaveText('241');
});
