import Ajv2020 from 'ajv/dist/2020';
import addFormats from 'ajv-formats';
import schema from './generated/api-schema.json';
import saved from './generated/saved-overview.json';
import metadata from './generated/metadata.json';
import type { components } from './generated/api-types';
import { RequestError } from './types';

type Name = 'ExploreResponse' | 'MetadataResponse' | 'ReportsResponse' | 'DetailResponse' | 'ErrorResponse';
const ajv = new Ajv2020({ strict: false, allErrors: false });
addFormats(ajv);
ajv.addSchema(schema, 'fda-api');
const validators = Object.fromEntries(
  (['ExploreResponse', 'MetadataResponse', 'ReportsResponse', 'DetailResponse', 'ErrorResponse'] as Name[])
    .map(name => [name, ajv.compile({ $ref: `fda-api#/components/schemas/${name}` })]),
);

export function checked<N extends Name>(name: N, value: unknown): components['schemas'][N] {
  if (!validators[name](value)) {
    throw new RequestError('INVALID_RESPONSE', 'The API returned data outside its checked contract.');
  }
  return value as components['schemas'][N];
}

export const bundledMetadata = checked('MetadataResponse', metadata);
export const savedOverview = checked('ExploreResponse', saved);
if (savedOverview.releaseId !== bundledMetadata.releaseId ||
    savedOverview.overview.datasetId !== bundledMetadata.metadata.datasetId ||
    savedOverview.overview.policyVersion !== bundledMetadata.metadata.policyVersion ||
    savedOverview.source !== 'prepared-default' ||
    JSON.stringify(savedOverview.overview.appliedFilters) !== JSON.stringify(bundledMetadata.metadata.defaultFilters)) {
  throw new Error('The saved overview does not match the bundled metadata.');
}
