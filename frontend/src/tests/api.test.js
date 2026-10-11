import { it, expect, vi, afterEach } from 'vitest';
import { requestAllocation, allocationUrl } from '../api.js';
afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
it('posts the exact bounded request to the real API path', async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ schema_version: 'heatshield.phase3a.v1' }) });
  vi.stubGlobal('fetch', fetch);
  await requestAllocation(29, 30);
  expect(fetch.mock.calls[0][0]).toBe('/api/allocations');
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ preset_id: 'synthetic_municipal_v1', budget_minor: 29, threshold_c: 30 });
});
it('surfaces structured server errors', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: { message: 'Invalid request', fields: { budget_minor: 'Out of range' } } }) }));
  await expect(requestAllocation(0, 30)).rejects.toThrow('Invalid request Out of range');
});
it('uses the configured production HTTPS origin and preserves exact request values', async () => {
  vi.stubEnv('VITE_API_BASE_URL', 'https://example.execute-api.ap-southeast-2.amazonaws.com/');
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal('fetch', fetch);
  await requestAllocation(7500001, 30);
  expect(fetch.mock.calls[0][0]).toBe('https://example.execute-api.ap-southeast-2.amazonaws.com/api/allocations');
  expect(JSON.parse(fetch.mock.calls[0][1].body).budget_minor).toBe(7500001);
});
it('defaults to the local proxy and rejects unsafe or ambiguous API bases', () => {
  expect(allocationUrl()).toBe('/api/allocations');
  for (const base of ['http://example.com', '/api', 'https://user:password@example.com', 'https://example.com/path', 'https://example.com?x=1', 'https://example.com#fragment', 'not a url']) {
    expect(() => allocationUrl(base)).toThrow();
  }
});
