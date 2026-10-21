import { afterEach, describe, expect, it, vi } from 'vitest';
import { getOverview, getReports } from '../src/api';
import { bundledMetadata, savedOverview } from '../src/contracts';

afterEach(() => vi.unstubAllGlobals());
const signal = () => new AbortController().signal;

describe('request context, bounded responses and raw search transport', () => {
  it('round-trips literal plus and spaces using URLSearchParams', async () => {
    const filters = { ...bundledMetadata.metadata.defaultFilters, productFilter: ' + CARROTS %_ ' };
    const payload = structuredClone(savedOverview);
    payload.overview.appliedFilters = filters;
    const fetcher = vi.fn(async (_url: string) => Response.json(payload));
    vi.stubGlobal('fetch', fetcher);
    await getOverview(filters, bundledMetadata, signal());
    const address = new URL(String(fetcher.mock.calls[0][0]), 'http://localhost');
    expect(address.searchParams.get('productFilter')).toBe(filters.productFilter);
    expect(address.searchParams.get('releaseId')).toBe(bundledMetadata.releaseId);
  });
  it('never accepts the prepared default as a different selection', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Response.json(savedOverview)));
    await expect(getOverview({ ...bundledMetadata.metadata.defaultFilters, productFilter: 'CARROTS' }, bundledMetadata, signal()))
      .rejects.toMatchObject({ code: 'RESPONSE_CONTEXT_MISMATCH' });
  });
  it('rejects another release even when response shape is valid', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Response.json({ ...savedOverview, releaseId: 'fda-release-sha256:' + '0'.repeat(64) })));
    await expect(getOverview(bundledMetadata.metadata.defaultFilters, bundledMetadata, signal())).rejects.toMatchObject({ code: 'RESPONSE_CONTEXT_MISMATCH' });
  });
  it('rejects oversized streamed responses without parsing a replacement', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('x'.repeat(1024 * 1024 + 1), { headers: { 'Content-Type': 'application/json' } })));
    await expect(getOverview(bundledMetadata.metadata.defaultFilters, bundledMetadata, signal())).rejects.toMatchObject({ code: 'RESPONSE_TOO_LARGE' });
  });
  it('does not automatically retry busy SQL work', async () => {
    const fetcher = vi.fn(async () => new Response('Busy', { status: 503 }));
    vi.stubGlobal('fetch', fetcher);
    await expect(getReports(bundledMetadata.metadata.defaultFilters, bundledMetadata, 25, null, signal())).rejects.toMatchObject({ code: 'SERVICE_BUSY' });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('treats proxy HTML as failure instead of no-match data', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('<html>Starting</html>', { headers: { 'Content-Type': 'text/html' } })));
    await expect(getOverview(bundledMetadata.metadata.defaultFilters, bundledMetadata, signal())).rejects.toMatchObject({ code: 'INVALID_RESPONSE' });
  });
});
