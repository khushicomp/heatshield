import React from 'react';
import { it, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import AllocationSummary from '../components/AllocationSummary.jsx';

function result(budget = 10000, spent = 7500) {
  return { allocation: { budget_minor: budget, spent_minor: spent, remaining_minor: budget - spent,
    selections: [{ option_id: 'cool_roof' }, { option_id: 'cool_roof' }, { option_id: 'shading' }, { option_id: 'baseline' }] },
    summary: { signed_avoided_kh: 12.34 }, buildings: [{}, {}, {}, {}] };
}
it('shows authoritative totals with accessible utilization and allocation counts', () => {
  render(<AllocationSummary result={result()}/>);
  expect(screen.getByText('₹75.00')).toBeTruthy();
  expect(screen.getByText('₹25.00')).toBeTruthy();
  expect(screen.getByText('12.34 K·h')).toBeTruthy();
  expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('75');
  const list = screen.getByRole('list', { name: 'Intervention distribution' });
  expect(within(list).getAllByRole('listitem').map(li => li.textContent)).toEqual(['No intervention 1', 'Cool roof 2', 'Roof shading 1']);
});
it('handles zero budget without nonfinite indicators', () => {
  render(<AllocationSummary result={result(0, 0)}/>);
  const bar = screen.getByRole('progressbar');
  expect(bar.getAttribute('aria-valuenow')).toBe('0');
  expect(bar.getAttribute('aria-valuetext')).toBe('No budget allocated');
  expect(screen.getByText('0.0%')).toBeTruthy();
});
