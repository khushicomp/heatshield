import { it, expect } from 'vitest';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { assetPaths, verifyBuild, verifyPublic } from '../../scripts/verify-build.mjs';
import { checkDeploymentOrigin } from '../../scripts/verify-deploy-env.mjs';
import { vi, afterEach } from 'vitest';
afterEach(() => vi.unstubAllGlobals());
const html = '<script type="module" src="/assets/main.js"></script><link rel="stylesheet" href="/assets/main.css">';

it('requires the existing HTTPS API origin for deploy builds', () => {
  expect(checkDeploymentOrigin('https://api.test')).toBe('https://api.test/api/allocations');
  for (const value of ['', undefined, 'http://api.test', 'https://REPLACE_API_ID.test', 'https://example.invalid']) expect(() => checkDeploymentOrigin(value)).toThrow();
});
it('rejects absent, nested or unsafe asset references', () => {
  expect(assetPaths(html)).toEqual(['/assets/main.js', '/assets/main.css']);
  for (const invalid of ['<div id="root"></div>', html.replace('/assets/main.js', '/dist/assets/main.js'), html.replace('/assets/main.js', '/assets/../main.js')]) expect(() => assetPaths(invalid)).toThrow();
});
it('fails when a referenced file is not in the published directory', async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'heatshield-build-'));
  try {
    await mkdir(path.join(dir, 'assets'));
    await writeFile(path.join(dir, 'index.html'), html);
    await writeFile(path.join(dir, 'assets/main.js'), 'console.log("fixture")');
    await expect(verifyBuild(dir)).rejects.toThrow();
    await writeFile(path.join(dir, 'assets/main.css'), 'body{}');
    await expect(verifyBuild(dir)).resolves.toHaveLength(2);
  } finally { await rm(dir, { recursive: true, force: true }); }
});
it('does not treat a 200 HTML rewrite as successful JavaScript delivery', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({ status: 200, headers: new Headers({ 'content-type': 'text/html' }), text: async () => html }).mockResolvedValueOnce({ status: 200, headers: new Headers({ 'content-type': 'text/html' }), text: async () => html }));
  await expect(verifyPublic('https://site.test')).rejects.toThrow('Public asset failed');
});
