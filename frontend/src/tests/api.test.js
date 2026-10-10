import { it, expect, vi, afterEach } from 'vitest';
import { requestAllocation } from '../api.js';
afterEach(() => vi.unstubAllGlobals());
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
