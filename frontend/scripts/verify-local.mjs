// Requires the Python API and Vite. All responses are real, not fixtures.
import assert from 'node:assert/strict';
import { requestAllocation } from '../src/api.js';
import { toPaise } from '../src/format.js';
const base = process.argv[2] || 'http://127.0.0.1:5173';
const nativeFetch = globalThis.fetch;
globalThis.fetch = (url, options) => nativeFetch(new URL(url, base), options);
const page = await fetch('/');
assert.equal(page.status, 200);
assert.match(await page.text(), /HeatShield/);
const result = await requestAllocation(toPaise('75000'), 30);
const a = result.allocation;
assert.equal(result.schema_version, 'heatshield.phase3a.v1');
assert.equal(a.spent_minor, 7470000);
assert.equal(a.remaining_minor, 30000);
assert.equal(a.score_units, '19380224213');
assert.equal(a.selections.length, 30);
assert.equal(new Set(a.selections.map(s => s.building_id)).size, 30);
assert.equal(a.selections.reduce((sum, s) => sum + s.cost_minor, 0), a.spent_minor);
assert.equal(a.selections.reduce((sum, s) => sum + BigInt(s.score_units), 0n).toString(), a.score_units);
assert.equal(a.selections.filter(s => s.option_id !== 'baseline').length, 24);
for (const b of result.buildings) for (const o of b.options) assert.equal(o.simulation.indoor_c.length, 168);
const direct = await nativeFetch('http://127.0.0.1:8000/api/allocations', {
  method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ preset_id: 'synthetic_municipal_v1', budget_minor: 7500000, threshold_c: 30 })
});
assert.equal(direct.status, 200);
const directText = await direct.text();
assert.deepEqual(result, JSON.parse(directText));
const zero = await requestAllocation(toPaise('0'), 30);
assert.equal(zero.allocation.spent_minor, 0);
assert.ok(zero.allocation.selections.every(s => s.option_id === 'baseline'));
await assert.rejects(() => requestAllocation(-1, 30), /Request validation failed/);
await assert.rejects(() => requestAllocation(0, 46), /Request validation failed/);
const malformed = await fetch('/api/allocations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{' });
assert.equal(malformed.status, 400);
console.log(JSON.stringify({ verified_proxy: base, status: 'PASS', buildings: 30, hours: 168,
  spent_minor: a.spent_minor, remaining_minor: a.remaining_minor, score_units: a.score_units,
  signed_avoided_kh: result.summary.signed_avoided_kh, response_bytes: Buffer.byteLength(directText),
  checks: 'frontend API client + exact money + proxy + direct reconciliation + zero budget + validation + malformed JSON'
}, null, 2));
