import type { components } from './generated/api-types';

export type Filters = components['schemas']['Filters'];
export type OverviewResponse = components['schemas']['ExploreResponse'];
export type MetadataResponse = components['schemas']['MetadataResponse'];
export type ReportsResponse = components['schemas']['ReportsResponse'];
export type DetailResponse = components['schemas']['DetailResponse'];
export type Report = components['schemas']['Report'];
export type Summary = components['schemas']['Summary'];
export type Overview = components['schemas']['Overview'];
export type Tab = 'overview' | 'reports' | 'source';
export type View = { filters: Filters; releaseId: string; tab: Tab; limit: number };

export class RequestError extends Error {
  constructor(public code: string, message: string, public status = 0, public retryable = false) {
    super(message);
    this.name = 'RequestError';
  }
}
