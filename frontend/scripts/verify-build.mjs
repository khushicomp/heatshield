import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

export function assetPaths(html) {
  const paths = [];
  for (const [tag] of html.matchAll(/<(?:script|link)\b[^>]*>/gi)) {
    if (/^<link/i.test(tag) && !/rel=["']stylesheet["']/i.test(tag)) continue;
    const ref = tag.match(/(?:src|href)=["']([^"']+)["']/i)?.[1];
    if (!ref || !/^\/assets\/[A-Za-z0-9_./-]+\.(?:js|css)$/.test(ref) || ref.includes('..') || ref.includes('//')) {
      throw new Error(`Invalid production asset reference: ${ref}`);
    }
    paths.push(ref);
  }
  if (!paths.some(p => p.endsWith('.js')) || !paths.some(p => p.endsWith('.css'))) {
    throw new Error('Production index must reference JavaScript and CSS under /assets/.');
  }
  return [...new Set(paths)];
}

export async function verifyBuild(directory = 'dist') {
  const refs = assetPaths(await readFile(path.join(directory, 'index.html'), 'utf8'));
  for (const ref of refs) {
    const file = path.join(directory, ref.slice(1));
    const info = await stat(file);
    if (!info.isFile() || !info.size) throw new Error(`Missing or empty build asset: ${ref}`);
  }
  return refs;
}

export async function verifyPublic(origin) {
  const root = new URL(origin);
  if (root.protocol !== 'https:' || root.pathname !== '/' || root.search || root.hash || root.username || root.password) throw new Error('Use the public HTTPS site origin.');
  const options = { headers: { 'Cache-Control': 'no-cache' }, signal: AbortSignal.timeout(20000) };
  const index = await fetch(root, options);
  if (index.status !== 200 || !index.headers.get('content-type')?.includes('text/html')) throw new Error(`Index: HTTP ${index.status}, ${index.headers.get('content-type')}`);
  const refs = assetPaths(await index.text());
  for (const ref of refs) {
    const response = await fetch(new URL(ref, root), { ...options, signal: AbortSignal.timeout(20000) });
    const type = response.headers.get('content-type') || '';
    const text = await response.text();
    const correctType = ref.endsWith('.css') ? type.includes('text/css') : /(?:javascript|ecmascript)/i.test(type);
    console.log(`${response.status} ${ref} (${type})`);
    if (response.status !== 200 || !correctType || !text.trim() || /^\s*(?:<!doctype html|<html)/i.test(text)) throw new Error(`Public asset failed: ${ref}`);
  }
  return refs;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const refs = process.argv[2] === '--url' ? await verifyPublic(process.argv[3]) : await verifyBuild(process.argv[2] || 'dist');
  console.log(`PASS: index and ${refs.length} referenced assets verified. This does not substitute for browser/API verification.`);
}
