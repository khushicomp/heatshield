import React from 'react';
import { it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
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
  expect(screen.getByText('Example building data — results have not been checked against real buildings')).toBeTruthy();
  expect(screen.getByText(/made-up \(synthetic\) example/)).toBeTruthy();
  expect(screen.getByText('See what your cooling budget could cover')).toBeTruthy();
  expect(screen.getByText(/One hour at 2 °C/)).toBeTruthy();
});
it('uses the API, preserves authoritative totals and exposes details and stale controls', async () => {
  requestAllocation.mockResolvedValue(fixture());
  render(<App/>);
  fireEvent.click(screen.getByRole('button', { name: 'Create cooling plan' }));
  await screen.findByText('₹1.23'); // Deliberately not recomputed from option costs.
  expect(requestAllocation).toHaveBeenCalledWith(7500000, 30);
  expect(screen.getByText('₹74,998.77')).toBeTruthy();
  expect(screen.getByText('12.34 K·h')).toBeTruthy();
  expect(screen.getByText('9007199254740999')).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'View Building 01 details' }));
  expect(screen.getByRole('dialog')).toBeTruthy();
  expect(screen.getByLabelText('How to read these estimates').textContent).toContain('walls, windows, floors and changes in ventilation');
  expect(screen.getByLabelText('How to read these estimates').textContent).toContain('roof, airflow, sunlight and how much heat the building stores');
  fireEvent.click(screen.getByText('Technical details: building inputs and sources'));
  expect(screen.getByText('Roof area (m²)')).toBeTruthy();
  expect(screen.getByText('40')).toBeTruthy();
  expect(screen.getByText(/more overheating/)).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: 'Close building details' }));
  expect(screen.queryByRole('dialog')).toBeNull();
  fireEvent.change(screen.getByLabelText('Total cooling budget (INR)'), { target: { value: '80000' } });
  expect(screen.getByText(/Settings changed/)).toBeTruthy();
});
it.each(['baseline', 'cool_roof'])('explains the citywide tradeoff without an individual counterfactual for %s', async selectedId => {
  const result = fixture();
  result.buildings[0].options.push({ option_id: 'cool_roof', cost_minor: 200, signed_avoided_kh: 10, simulation: { indoor_c: [28,29] } });
  result.allocation.selections[0].option_id = selectedId;
  requestAllocation.mockResolvedValue(result);
  render(<App/>);
  fireEvent.click(screen.getByRole('button', { name: 'Create cooling plan' }));
  fireEvent.click(await screen.findByRole('button', { name: 'View Building 01 details' }));
  const explanation = screen.getByRole('region', { name: 'Understanding this cooling plan' });
  expect(within(explanation).getByRole('heading', { level: 3 }).textContent).toBe('Understanding this cooling plan');
  expect(explanation.textContent).toContain('largest total estimated reduction in overheating across all buildings, without going over your budget');
  expect(explanation.textContent).toContain('at most one improvement');
  expect(explanation.textContent).toContain('not a calculated reason');
  expect(explanation.textContent).toContain('different improvement, or none for this building');
  expect(explanation.textContent).toContain('less money for other buildings');
  expect(explanation.textContent).toContain('We have not calculated how choosing a different improvement here would change the rest of the plan');
  const dialog = screen.getByRole('dialog');
  expect(within(dialog).getByText(selectedId === 'baseline' ? 'No improvement · in this plan' : 'Reflective roof (cool roof) · in this plan')).toBeTruthy();
  expect(within(dialog).getByText(/more overheating/)).toBeTruthy();
  expect(within(dialog).getByRole('img', { name: /Estimated indoor temperatures without improvements/ })).toBeTruthy();
  expect(within(dialog).getByText('Technical details: building inputs and sources')).toBeTruthy();
  expect(within(dialog).getByLabelText('How to read these estimates')).toBeTruthy();
  expect(within(dialog).getByText('-4')).toBeTruthy();
  fireEvent.click(within(dialog).getByText('View hourly temperatures as a table'));
  expect(within(dialog).getAllByText('30.00').length).toBeGreaterThan(0);
  expect(within(dialog).getAllByText(selectedId === 'baseline' ? '31.00' : '28.00').length).toBeGreaterThan(0);
});
it('explains the temperature setting and rejects invalid values before calling the service', async () => {
  render(<App/>);
  const temperature = screen.getByLabelText('Temperature limit for comparison (°C)');
  expect(temperature.getAttribute('aria-describedby')).toBe('temperature-help');
  expect(screen.getByText(/this is not a health or safety limit/)).toBeTruthy();
  fireEvent.change(temperature, { target: { value: '46' } });
  fireEvent.submit(screen.getByRole('button', { name: 'Create cooling plan' }).closest('form'));
  expect((await screen.findByRole('alert')).textContent).toContain('between 15 and 45 °C');
  expect(requestAllocation).not.toHaveBeenCalled();
});
it('keeps the previous plan and labels it clearly when an updated request fails', async () => {
  requestAllocation.mockResolvedValueOnce(fixture()).mockRejectedValueOnce(new Error('No new plan was created.'));
  render(<App/>);
  fireEvent.click(screen.getByRole('button', { name: 'Create cooling plan' }));
  await screen.findByText('₹1.23');
  fireEvent.change(screen.getByLabelText('Total cooling budget (INR)'), { target: { value: '80000' } });
  fireEvent.click(screen.getByRole('button', { name: 'Create cooling plan' }));
  expect((await screen.findByRole('alert')).textContent).toContain('Your previous cooling plan is still shown below');
  expect(screen.getByText('₹1.23')).toBeTruthy();
  expect(screen.getByText(/Plan shown: INR 75000 budget/)).toBeTruthy();
});
it('shows loading then a recoverable API error', async () => {
  let reject;
  requestAllocation.mockImplementation(() => new Promise((_, no) => { reject = no; }));
  render(<App/>);
  fireEvent.click(screen.getByRole('button', { name: 'Create cooling plan' }));
  expect(screen.getByRole('button', { name: 'Creating your plan…' }).disabled).toBe(true);
  reject(new Error('This plan needs more calculation than the demo allows. No new plan was created.'));
  expect((await screen.findByRole('alert')).textContent).toContain('No new plan was created');
  await waitFor(() => expect(screen.getByRole('button', { name: 'Create cooling plan' }).disabled).toBe(false));
});
it('blocks imprecise money before calling the API', async () => {
  render(<App/>);
  fireEvent.change(screen.getByLabelText('Total cooling budget (INR)'), { target: { value: '0.005' } });
  fireEvent.click(screen.getByRole('button', { name: 'Create cooling plan' }));
  expect((await screen.findByRole('alert')).textContent).toContain('two decimal');
  expect(requestAllocation).not.toHaveBeenCalled();
});
