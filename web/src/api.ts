import { checked, bundledMetadata } from './contracts';
import { binaryCompare, sameFilters } from './selection';
import { RequestError } from './types';
import type { Filters, MetadataResponse } from './types';

const prefix = '/api/v1/fda/';
const maximumBytes = 1024 * 1024;

async function jsonRequest(path: string, signal: AbortSignal, milliseconds = 35000): Promise<unknown> {
  const deadline = AbortSignal.timeout(milliseconds);
  try {
    const response = await fetch(prefix + path, {
      signal: AbortSignal.any([signal, deadline]), cache: 'no-store', headers: { Accept: 'application/json' },
    });
    const reader = response.body?.getReader();
    const chunks: Uint8Array[] = [];
    let length = 0;
    if (reader) {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          length += value.byteLength;
          if (length > maximumBytes) {
            await reader.cancel();
            throw new RequestError('RESPONSE_TOO_LARGE', 'The response exceeded the checked size limit.');
          }
          chunks.push(value);
        }
      } finally { reader.releaseLock(); }
    }
    const bytes = new Uint8Array(length);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    let value: unknown;
    try { value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)); } catch { value = null; }
    if (!response.ok) {
      let code = response.status === 429 ? 'RATE_LIMITED' : response.status === 503 ? 'SERVICE_BUSY' : 'HTTP_ERROR';
      let retryable = response.status >= 500 || response.status === 429;
      try {
        const error = checked('ErrorResponse', value).error;
        code = error.code;
        retryable = error.retryable;
      } catch { /* A proxy/server may reject before the JSON application boundary. */ }
      throw new RequestError(code, 'The request could not be completed.', response.status, retryable);
    }
    if (!response.headers.get('content-type')?.includes('application/json') || value === null) {
      throw new RequestError('INVALID_RESPONSE', 'The API returned an invalid JSON response.');
    }
    return value;
  } catch (error) {
    if (signal.aborted) throw error;
    if (deadline.aborted) throw new RequestError('REQUEST_TIMEOUT', 'The request timed out.', 0, true);
    if (error instanceof RequestError) throw error;
    throw new RequestError('NETWORK_ERROR', 'The API could not be reached.', 0, true);
  }
}

function query(filters: Filters, metadata: MetadataResponse): URLSearchParams {
  const params = new URLSearchParams({ releaseId: metadata.releaseId,
    startYear: String(filters.startYear), endYear: String(filters.endYear) });
  if (filters.productFilter !== null) params.set('productFilter', filters.productFilter);
  return params;
}

function identity(value: { releaseId: string; snapshotAcquiredAt: string }, context: {
  datasetId: string; policyVersion: string; appliedFilters?: Filters;
}, metadata: MetadataResponse, filters?: Filters) {
  if (value.releaseId !== metadata.releaseId || value.snapshotAcquiredAt !== metadata.snapshotAcquiredAt ||
      context.datasetId !== metadata.metadata.datasetId || context.policyVersion !== metadata.metadata.policyVersion ||
      (filters && (!context.appliedFilters || !sameFilters(context.appliedFilters, filters)))) {
    throw new RequestError('RESPONSE_CONTEXT_MISMATCH', 'The response belongs to another snapshot or selection.');
  }
}

export async function getMetadata(signal: AbortSignal) {
  const params = new URLSearchParams({ releaseId: bundledMetadata.releaseId });
  const result = checked('MetadataResponse', await jsonRequest('metadata?' + params, signal, 8000));
  identity(result, result.metadata, bundledMetadata);
  return result;
}

function delay(milliseconds: number, signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    if (signal.aborted) return reject(signal.reason);
    const cancelled = () => { clearTimeout(timer); reject(signal.reason); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', cancelled); resolve(); }, milliseconds);
    signal.addEventListener('abort', cancelled, { once: true });
  });
}

export async function connect(signal: AbortSignal) {
  for (let attempt = 0; attempt < 3; attempt++) {
    try { return await getMetadata(signal); } catch (error) {
      if (signal.aborted || !(error instanceof RequestError) || !error.retryable || attempt === 2) throw error;
      await delay((attempt + 1) * 2000, signal);
    }
  }
  throw new Error('Connection attempts exhausted.');
}

export async function getOverview(filters: Filters, metadata: MetadataResponse, signal: AbortSignal) {
  const result = checked('ExploreResponse', await jsonRequest('explore?' + query(filters, metadata), signal));
  identity(result, result.overview, metadata, filters);
  return result;
}

export async function getReports(filters: Filters, metadata: MetadataResponse, limit: number, cursor: string | null, signal: AbortSignal) {
  const params = query(filters, metadata);
  params.set('limit', String(limit));
  params.set('sort', 'reportId:asc');
  if (cursor) params.set('cursor', cursor);
  const result = checked('ReportsResponse', await jsonRequest('reports?' + params, signal));
  identity(result, result.page, metadata, filters);
  const ids = result.page.items.map(item => item.reportId);
  if (result.page.limit !== limit || result.page.returnedCount !== ids.length || ids.length > limit ||
      ids.some((id, index) => index > 0 && binaryCompare(id, ids[index - 1]) <= 0) || result.page.hasMore !== (result.page.nextCursor !== null)) {
    throw new RequestError('INVALID_RESPONSE', 'The report page did not match its checked bounds or order.');
  }
  return result;
}

export async function getDetail(filters: Filters, metadata: MetadataResponse, reportId: string, signal: AbortSignal) {
  const params = query(filters, metadata);
  params.set('reportId', reportId);
  const result = checked('DetailResponse', await jsonRequest('reports/detail?' + params, signal));
  identity(result, result.detail, metadata, filters);
  if (result.detail.report.reportId !== reportId) throw new RequestError('INVALID_RESPONSE', 'A different report was returned.');
  return result;
}

export function errorMessage(error: unknown): string {
  const code = error instanceof RequestError ? error.code : '';
  if (code === 'RELEASE_MISMATCH' || code === 'RESPONSE_CONTEXT_MISMATCH') {
    return 'The API snapshot does not match this saved view. No different snapshot or selection has been substituted.';
  }
  if (code === 'SERVICE_BUSY') return 'The API is busy. The request was not queued; try again shortly.';
  if (code === 'RATE_LIMITED') return 'The service request limit was reached. Try again later.';
  if (code === 'QUERY_TIMEOUT' || code === 'REQUEST_TIMEOUT') return 'The request timed out. Previous results have not been replaced.';
  if (code === 'INVALID_PARAMETER') return 'The API rejected this selection. Check the year range and product text.';
  if (code === 'RESPONSE_TOO_LARGE') return 'This response exceeds the checked size limit. No data was truncated.';
  if (code === 'REPORT_NOT_FOUND') return 'This report is not available in the applied selection.';
  if (code === 'INVALID_RESPONSE') return 'The response failed contract validation. Its data has not been displayed.';
  return 'The API is unavailable. Only the explicitly labeled saved or previously received results remain available.';
}
