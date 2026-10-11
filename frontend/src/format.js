export const MAX_BUDGET = 100000000n;
export function toPaise(text) {
  if (!/^\d+(\.\d{1,2})?$/.test(text)) throw new Error('Enter your budget in rupees without commas, using at most two decimal places (for example, 75000 or 75000.50).');
  const [whole, fraction = ''] = text.split('.');
  const paise = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'));
  if (paise > MAX_BUDGET) throw new Error('Enter a budget between INR 0 and INR 10,00,000.');
  return Number(paise); // Bounded integer; no floating-point money arithmetic.
}
export function money(paise) {
  const value = BigInt(paise);
  return `₹${(value / 100n).toLocaleString('en-IN')}.${(value % 100n).toString().padStart(2, '0')}`;
}
export const kh = value => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(value);
export const optionName = id => ({ baseline: 'No improvement', cool_roof: 'Reflective roof (cool roof)', insulation: 'Roof insulation', shading: 'Roof shading' })[id] || id;
