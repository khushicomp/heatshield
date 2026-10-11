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
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, json: async () => ({ error: { code: 'VALIDATION_ERROR', fields: { budget_minor: 'Out of range', threshold_c: 'Out of range' } } }) }));
  await expect(requestAllocation(0, 30)).rejects.toThrow('Enter a budget from INR 0 to INR 10,00,000');
  await expect(requestAllocation(0, 30)).rejects.toThrow('Choose a temperature limit between 15 and 45 °C.');
});
it.each([
  ['OPTIMIZATION_STATE_LIMIT', 422, 'No new plan was created'],
  [undefined, 429, 'Wait a moment'],
  ['INTERNAL_ERROR', 500, 'We could not create your cooling plan']
])('gives a plain-language next step for %s errors', async (code, status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status, json: async () => ({ error: { code, message: 'Technical server detail' } }) }));
  await expect(requestAllocation(0, 30)).rejects.toThrow(message);
  await expect(requestAllocation(0, 30)).rejects.not.toThrow('Technical server detail');
});
it('explains connection and unreadable-response failures', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
  await expect(requestAllocation(0, 30)).rejects.toThrow('Check your connection and try again');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ json: async () => { throw new SyntaxError(); } }));
  await expect(requestAllocation(0, 30)).rejects.toThrow('unreadable response');
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
