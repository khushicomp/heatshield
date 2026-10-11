export function allocationUrl(base = '') {
  if (!base) return '/api/allocations';
  let url;
  try { url = new URL(base); } catch { throw new Error('The calculation service address is not set up correctly. Please contact the site owner.'); }
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw new Error('The calculation service address is not set up correctly. Please contact the site owner.');
  }
  return `${url.origin}/api/allocations`;
}

export async function requestAllocation(budget_minor, threshold_c) {
  const url = allocationUrl(import.meta.env?.VITE_API_BASE_URL || '');
  let response;
  try {
    response = await fetch(url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preset_id: 'synthetic_municipal_v1', budget_minor, threshold_c })
    });
  } catch {
    throw new Error('We could not reach the calculation service. Check your connection and try again.');
  }
  let payload;
  try { payload = await response.json(); }
  catch { throw new Error('The calculation service sent an unreadable response. Please try again.'); }
  if (!response.ok) {
    const error = payload.error;
    if (error?.code === 'VALIDATION_ERROR') {
      const messages = [];
      if (error.fields?.budget_minor) messages.push('Enter a budget from INR 0 to INR 10,00,000, with no more than two decimal places.');
      if (error.fields?.threshold_c) messages.push('Choose a temperature limit between 15 and 45 °C.');
      if (error.fields?.preset_id || error.fields?.request) messages.push('The example plan could not be loaded. Refresh the page and try again.');
      throw new Error(messages.join(' ') || 'Check your budget and temperature limit, then try again.');
    }
    if (error?.code === 'OPTIMIZATION_STATE_LIMIT') throw new Error('This plan needs more calculation than the demo allows. Try a smaller budget. No new plan was created.');
    if (response.status === 429) throw new Error('The service is busy. Wait a moment, then try again.');
    throw new Error('We could not create your cooling plan. Please try again. No new plan was created.');
  }
  return payload;
}
