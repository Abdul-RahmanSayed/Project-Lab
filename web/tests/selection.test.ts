import { describe, expect, it } from 'vitest';
import { bundledMetadata, savedOverview, checked } from '../src/contracts';
import { binaryCompare, defaultView, draftFilters, encodeView, firstPage, nextPage, parseView, previousPage, sameFilters } from '../src/selection';

const defaults = bundledMetadata.metadata.defaultFilters;

describe('exact selection and shareable state', () => {
  it('preserves raw spaces, punctuation, case, plus and Unicode without normalizing', () => {
    for (const product of [' CARROTS ', '%', '_', '+', 'Stra\u00dfe', 'null', '<img src=x onerror=alert(1)>']) {
      const filters = draftFilters('2024', '2026', product, defaults);
      expect(filters.productFilter).toBe(product);
      const view = { ...defaultView(bundledMetadata), filters, tab: 'reports' as const, limit: 100 };
      expect(parseView(encodeView(view, bundledMetadata), bundledMetadata)).toEqual({ view });
    }
  });
  it('distinguishes empty controls from whitespace-only searches', () => {
    expect(draftFilters('2002', '2026', '', defaults).productFilter).toBeNull();
    expect(() => draftFilters('2002', '2026', '   ', defaults)).toThrow();
  });
  it('uses Python-compatible code-point and UTF-8 text bounds', () => {
    expect(draftFilters('2002', '2026', '\u{1f600}'.repeat(256), defaults).productFilter).toHaveLength(512);
    expect(() => draftFilters('2002', '2026', '\u{1f600}'.repeat(257), defaults)).toThrow();
  });
  it('rejects invalid years rather than quietly clamping them', () => {
    for (const [start, end] of [['2026', '2024'], ['2001', '2025'], ['2002', '2027'], ['2024.0', '2025'], ['true', '2025']]) {
      expect(() => draftFilters(start, end, '', defaults)).toThrow();
    }
  });
  it('defaults the view without a personal-persistence override', () => {
    expect(parseView('', bundledMetadata)).toEqual({ view: defaultView(bundledMetadata) });
    const hash = encodeView(defaultView(bundledMetadata), bundledMetadata);
    expect(hash).toContain('releaseId=');
    expect(hash).not.toContain('startYear');
    expect(hash).not.toContain('sort');
  });
  it('rejects malformed, duplicate, unknown, wrong-release and unsupported URL settings', () => {
    for (const query of ['startYear=2026&endYear=2024', 'productFilter=%FF', 'productFilter=%QZ', 'productFilter=',
      'productFilter=+++', 'startYear=2024&startYear=2025', 'sql=1', 'tab=unknown', 'limit=101', 'sort=age:desc',
      'releaseId=fda-release-sha256:' + '0'.repeat(64)]) {
      expect(parseView('#/fda?' + query, bundledMetadata).error, query).toBeTruthy();
    }
    expect(parseView('#/other', bundledMetadata).error).toBeTruthy();
  });
  it('does not treat differently cased or spaced filters as interchangeable', () => {
    expect(sameFilters({ ...defaults, productFilter: 'CARROTS' }, { ...defaults, productFilter: 'carrots' })).toBe(false);
    expect(sameFilters({ ...defaults, productFilter: 'CARROTS ' }, { ...defaults, productFilter: 'CARROTS' })).toBe(false);
  });
  it('validates report-ID order as UTF-8 BINARY, not JavaScript UTF-16 order', () => {
    expect(binaryCompare('\u{10000}', '\ue000')).toBeGreaterThan(0);
    expect(binaryCompare('2024-CFS-001', '2024-CFS-002')).toBeLessThan(0);
    expect(binaryCompare('same', 'same')).toBe(0);
  });
  it('bounds bookmark history without caching report rows', () => {
    let page = firstPage();
    for (let index = 1; index <= 150; index++) page = nextPage(page, 'cursor-' + index);
    expect(page.number).toBe(151);
    expect(page.previous).toHaveLength(100);
    expect(previousPage(page).cursor).toBe('cursor-149');
    expect(Object.keys(page).sort()).toEqual(['cursor', 'number', 'previous']);
    expect(firstPage().cursor).toBeNull();
  });
});

describe('generated response contracts and saved bundle', () => {
  it('validates real checked responses and release-bound defaults', () => {
    expect(checked('ExploreResponse', savedOverview)).toEqual(savedOverview);
    expect(savedOverview.releaseId).toBe(bundledMetadata.releaseId);
    expect(savedOverview.overview.selectedCount).toBe(97652);
    expect(sameFilters(savedOverview.overview.appliedFilters, defaults)).toBe(true);
  });
  it('rejects missing arrays, string counts and invented extra fields', () => {
    for (const mutate of [
      (value: typeof savedOverview) => { (value.overview as unknown as Record<string, unknown>).selectedCount = '97652'; },
      (value: typeof savedOverview) => { delete (value.overview as unknown as Record<string, unknown>).ageHistogram; },
      (value: typeof savedOverview) => { Object.assign(value.overview, { invented: true }); },
    ]) {
      const value = structuredClone(savedOverview);
      mutate(value);
      expect(() => checked('ExploreResponse', value)).toThrow();
    }
  });
});
