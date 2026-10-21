import type { Filters, MetadataResponse, View } from './types';

export const sameFilters = (a: Filters, b: Filters) => a.startYear === b.startYear &&
  a.endYear === b.endYear && a.productFilter === b.productFilter;
export const filterKey = (filters: Filters) => JSON.stringify([filters.startYear, filters.endYear, filters.productFilter]);
export function binaryCompare(a: string, b: string) {
  const encoder = new TextEncoder(), left = encoder.encode(a), right = encoder.encode(b);
  for (let index = 0; index < Math.min(left.length, right.length); index++) {
    if (left[index] !== right[index]) return left[index] - right[index];
  }
  return left.length - right.length;
}
export const selectionLabel = (filters: Filters) => `${filters.startYear}-${filters.endYear} / ${
  filters.productFilter === null ? 'All suspect products' : `Raw product contains "${filters.productFilter}"`}`;

export function defaultView(metadata: MetadataResponse): View {
  return { filters: metadata.metadata.defaultFilters, releaseId: metadata.releaseId, tab: 'overview', limit: 25 };
}

export function draftFilters(start: string, end: string, product: string, bounds: Filters): Filters {
  if (!/^\d{4}$/.test(start) || !/^\d{4}$/.test(end)) throw new Error('Choose a valid start and end year.');
  const startYear = Number(start), endYear = Number(end);
  if (startYear < bounds.startYear || endYear > bounds.endYear || startYear > endYear) {
    throw new Error(`Choose an ordered year range within ${bounds.startYear}-${bounds.endYear}.`);
  }
  if (product !== '' && (!product.trim() || [...product].length > 256 || new TextEncoder().encode(product).length > 1024)) {
    throw new Error('Product text must be nonblank, at most 256 characters and 1,024 UTF-8 bytes.');
  }
  return { startYear, endYear, productFilter: product === '' ? null : product };
}

export function parseView(hash: string, metadata: MetadataResponse): { view: View; error?: string } {
  const initial = defaultView(metadata);
  try {
    if (!hash || hash === '#' || hash === '#/' || hash === '#/fda') return { view: initial };
    if (!hash.startsWith('#/fda?') || hash.length > 8193) throw new Error('This shared view has an unsupported address.');
    const raw = hash.slice(6);
    decodeURIComponent(raw.replace(/\+/g, ' '));
    const params = new URLSearchParams(raw);
    const allowed = new Set(['startYear', 'endYear', 'productFilter', 'releaseId', 'tab', 'limit', 'sort']);
    if ([...params.keys()].some(key => !allowed.has(key) || params.getAll(key).length !== 1)) {
      throw new Error('This shared view contains unknown or repeated settings.');
    }
    const releaseId = params.get('releaseId') ?? metadata.releaseId;
    if (releaseId !== metadata.releaseId) throw new Error('This shared view belongs to a different saved snapshot.');
    if (params.has('productFilter') && params.get('productFilter') === '') throw new Error('This shared view contains an empty product search.');
    const filters = draftFilters(params.get('startYear') ?? String(initial.filters.startYear),
      params.get('endYear') ?? String(initial.filters.endYear), params.get('productFilter') ?? '', initial.filters);
    const tab = params.get('tab') ?? 'overview';
    if (!['overview', 'reports', 'source'].includes(tab)) throw new Error('This shared view has an unsupported tab.');
    const limit = params.get('limit') ?? '25';
    if (!['25', '50', '100'].includes(limit) || (params.get('sort') ?? 'reportId:asc') !== 'reportId:asc') {
      throw new Error('This shared view has unsupported page or sort settings.');
    }
    return { view: { filters, releaseId, tab: tab as View['tab'], limit: Number(limit) } };
  } catch (error) {
    return { view: initial, error: error instanceof Error ? error.message : 'This shared view could not be read.' };
  }
}

export function encodeView(view: View, metadata: MetadataResponse): string {
  const params = new URLSearchParams({ releaseId: view.releaseId });
  if (view.filters.startYear !== metadata.metadata.defaultFilters.startYear) params.set('startYear', String(view.filters.startYear));
  if (view.filters.endYear !== metadata.metadata.defaultFilters.endYear) params.set('endYear', String(view.filters.endYear));
  if (view.filters.productFilter !== null) params.set('productFilter', view.filters.productFilter);
  if (view.tab !== 'overview') params.set('tab', view.tab);
  if (view.limit !== 25) params.set('limit', String(view.limit));
  return '#/fda?' + params.toString();
}

export type PagePosition = { cursor: string | null; previous: (string | null)[]; number: number };
export const firstPage = (): PagePosition => ({ cursor: null, previous: [], number: 1 });
export const nextPage = (page: PagePosition, cursor: string): PagePosition => ({
  cursor, previous: [...page.previous, page.cursor].slice(-100), number: page.number + 1,
});
export const previousPage = (page: PagePosition): PagePosition => page.previous.length ? ({
  cursor: page.previous.at(-1) ?? null, previous: page.previous.slice(0, -1), number: page.number - 1,
}) : firstPage();
