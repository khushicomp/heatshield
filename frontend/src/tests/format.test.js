import { describe, it, expect } from 'vitest';
import { toPaise, money } from '../format.js';
describe('Exact money', () => {
  it('converts decimal text using integer arithmetic', () => {
    expect(toPaise('0.29')).toBe(29);
    expect(toPaise('75000.01')).toBe(7500001);
    expect(toPaise('0001.2')).toBe(120);
    expect(toPaise('0')).toBe(0);
    expect(toPaise('1000000')).toBe(100000000);
    expect(money(7470000)).toBe('₹74,700.00');
  });
  it('rejects fractional paise, overflow and unsupported text', () => {
    for (const v of ['1.005', '1000000.01', '-1', 'NaN', '', '1e3', '75,000', ' 1', '.50']) expect(() => toPaise(v)).toThrow();
  });
});
