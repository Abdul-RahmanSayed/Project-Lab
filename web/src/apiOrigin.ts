export function apiOrigin(value: string | undefined): string {
  if (value === undefined || value === '') return '';
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash ||
      url.pathname !== '/' || (value !== url.origin && value !== url.origin + '/')) {
    throw new Error('The API origin must be a plain HTTPS origin without a path or credentials.');
  }
  return url.origin;
}
