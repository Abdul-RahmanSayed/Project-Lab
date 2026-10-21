import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const directory = new URL('../src/generated/', import.meta.url);
const manifest = JSON.parse(await readFile(new URL('bundle.json', directory), 'utf8'));
for (const [name, expected] of Object.entries(manifest.files)) {
  const bytes = await readFile(new URL(name, directory));
  if (bytes.length !== expected.bytes || createHash('sha256').update(bytes).digest('hex') !== expected.sha256) {
    throw new Error(`Saved frontend bundle changed: ${name}. Regenerate it from the selected checked release.`);
  }
}
const overview = JSON.parse(await readFile(new URL('saved-overview.json', directory), 'utf8'));
const metadata = JSON.parse(await readFile(new URL('metadata.json', directory), 'utf8'));
const schema = JSON.parse(await readFile(new URL('api-schema.json', directory), 'utf8'));
if (overview.releaseId !== manifest.releaseId || metadata.releaseId !== manifest.releaseId ||
    schema['x-project-lab-release'] !== manifest.releaseId ||
    overview.overview.datasetId !== metadata.metadata.datasetId ||
    overview.overview.policyVersion !== metadata.metadata.policyVersion ||
    JSON.stringify(overview.overview.appliedFilters) !== JSON.stringify(metadata.metadata.defaultFilters)) {
  throw new Error('The saved frontend artifacts belong to different releases or default selections.');
}
console.log(`Checked saved frontend bundle: ${manifest.releaseId}`);
