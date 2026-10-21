import { describe, expect, it } from 'vitest';
import { apiOrigin } from '../src/apiOrigin';

describe('trusted build-time API origin', () => {
  it('preserves the local proxy when no origin is configured', () => {
    expect(apiOrigin(undefined)).toBe('');
    expect(apiOrigin('')).toBe('');
  });
  it('accepts a plain HTTPS origin and strips only the optional root slash', () => {
    expect(apiOrigin('https://example.onrender.com/')).toBe('https://example.onrender.com');
    expect(apiOrigin('https://127.0.0.1:8767')).toBe('https://127.0.0.1:8767');
  });
  it('rejects insecure, credentialed, path-based, malformed and URL-state origins', () => {
    for (const value of ['http://example.com', '//example.com', '/api', 'https://u:p@example.com',
      'https://example.com/Project-Lab/', 'https://example.com?x=1', 'https://example.com#x',
      ' https://example.com', 'https://EXAMPLE.COM', 'https://example.com:443']) {
      expect(() => apiOrigin(value), value).toThrow();
    }
  });
});
