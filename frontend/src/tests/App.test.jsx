import React from 'react';
import { it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App.jsx';
import { requestAllocation } from '../api.js';
vi.mock('../api.js', () => ({ requestAllocation: vi.fn() }));
vi.mock('recharts', () => Object.fromEntries(['ResponsiveContainer','LineChart','Line','XAxis','YAxis','CartesianGrid','Tooltip','ReferenceLine','Legend'].map(name => [name, ({ children }) => <div>{children}</div>])));
afterEach(() => vi.resetAllMocks());
function fixture() {
  return { allocation: { budget_minor: 7500000, spent_minor: 123, remaining_minor: 7499877, score_units: '9007199254740999', selections: [{ building_id: 'demo_01', option_id: 'baseline' }] }, summary: { signed_avoided_kh: 12.34 }, buildings: [{ building_id: 'demo_01', building: { roof_area_m2: 40 }, source: { kind: 'synthetic', description: 'Fixture' }, options: [{ option_id: 'baseline', cost_minor: 0, signed_avoided_kh: 0, simulation: { indoor_c: [30,31] } }, { option_id: 'insulation', cost_minor: 100, signed_avoided_kh: -4, simulation: { indoor_c: [32,33] } }] }], weather: [], assumptions: ['Provisional fixture'], limitations: [{ code: 'UNVALIDATED', text: 'Not validated' }], horizon_hours: 2, threshold_c: 30 };
}
it('shows empty state and prominent scientific caveats', () => {
  render(<App/>);
  expect(screen.getByText('Synthetic scenario — not empirically validated')).toBeTruthy();
  expect(screen.getByText('Roof-dominated synthetic stress scenario')).toBeTruthy();
  expect(screen.getByText('A clearer view of cooling choices')).toBeTruthy();
  expect(screen.getByText(/One hour at 2 °C/)).toBeTruthy();
});
it('uses the API, preserves authoritative totals and exposes details and stale controls', async () => {
  requestAllocation.mockResolvedValue(fixture());
  render(<App/>);
  fireEvent.click(screen.getByRole('button', { name: 'Run allocation' }));
  await screen.findByText('₹1.23'); // Deliberately not recomputed from option costs.
  expect(requestAllocation).toHaveBeenCalledWith(7500000, 30);
  expect(screen.getByText('₹74,998.77')).toBeTruthy();
  expect(screen.getByText('12.34 K·h')).toBeTruthy();
  expect(screen.getByText('9007199254740999')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Inspect demo_01' }));
  expect(screen.getByRole('dialog')).toBeTruthy();
  expect(screen.getByLabelText('Scenario interpretation').textContent).toContain('Walls, windows, floors and variable ventilation');
  expect(screen.getByLabelText('Scenario interpretation').textContent).toContain('provisional roof, ventilation, solar and capacitance');
  expect(screen.getByText('Roof area (m?)')).toBeTruthy();
  expect(screen.getByText('40')).toBeTruthy();
  expect(screen.getByText(/increases overheating/)).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Close building details' }));
  expect(screen.queryByRole('dialog')).toBeNull();
  fireEvent.change(screen.getByLabelText('Municipal budget (INR)'), { target: { value: '80000' } });
  expect(screen.getByText(/Controls changed/)).toBeTruthy();
});
it('shows loading then a recoverable API error', async () => {
  let reject;
  requestAllocation.mockImplementation(() => new Promise((_, no) => { reject = no; }));
  render(<App/>);
  fireEvent.click(screen.getByRole('button', { name: 'Run allocation' }));
  expect(screen.getByRole('button', { name: 'Running allocation…' }).disabled).toBe(true);
  reject(new Error('Optimizer state limit exceeded; no allocation was returned.'));
  expect((await screen.findByRole('alert')).textContent).toContain('state limit');
  await waitFor(() => expect(screen.getByRole('button', { name: 'Run allocation' }).disabled).toBe(false));
});
it('blocks imprecise money before calling the API', async () => {
  render(<App/>);
  fireEvent.change(screen.getByLabelText('Municipal budget (INR)'), { target: { value: '0.005' } });
  fireEvent.click(screen.getByRole('button', { name: 'Run allocation' }));
  expect((await screen.findByRole('alert')).textContent).toContain('two decimal');
  expect(requestAllocation).not.toHaveBeenCalled();
});
