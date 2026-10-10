export const MAX_BUDGET = 100000000n;
export function toPaise(text) {
  if (!/^\d+(\.\d{1,2})?$/.test(text)) throw new Error('Enter INR with at most two decimal places, without commas.');
  const [whole, fraction = ''] = text.split('.');
  const paise = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'));
  if (paise > MAX_BUDGET) throw new Error('Budget must be between INR 0 and INR 10,00,000.');
  return Number(paise); // Bounded integer; no floating-point money arithmetic.
}
export function money(paise) {
  const value = BigInt(paise);
  return `₹${(value / 100n).toLocaleString('en-IN')}.${(value % 100n).toString().padStart(2, '0')}`;
}
export const kh = value => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(value);
export const optionName = id => ({ baseline: 'No intervention', cool_roof: 'Cool roof', insulation: 'Roof insulation', shading: 'Roof shading' })[id] || id;
