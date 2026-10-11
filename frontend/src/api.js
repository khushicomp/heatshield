export function allocationUrl(base = '') {
  if (!base) return '/api/allocations';
  let url;
  try { url = new URL(base); } catch { throw new Error('API base URL must be an HTTPS origin.'); }
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw new Error('API base URL must be an HTTPS origin without a path, credentials, query or fragment.');
  }
  return `${url.origin}/api/allocations`;
}

export async function requestAllocation(budget_minor, threshold_c) {
  const response = await fetch(allocationUrl(import.meta.env?.VITE_API_BASE_URL || ''), {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preset_id: 'synthetic_municipal_v1', budget_minor, threshold_c })
  });
  const payload = await response.json();
  if (!response.ok) {
    const error = payload.error;
    throw new Error(`${error?.message || 'Allocation failed.'} ${Object.values(error?.fields || {}).join(' ')}`.trim());
  }
  return payload;
}
