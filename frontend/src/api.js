export async function requestAllocation(budget_minor, threshold_c) {
  const response = await fetch('/api/allocations', {
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
