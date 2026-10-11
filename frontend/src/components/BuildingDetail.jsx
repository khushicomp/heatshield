import { useEffect, useRef } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Legend } from 'recharts';
import { kh, money, optionName } from '../format.js';
const parameterLabels = {
  archetype: 'Roof type',
  roof_area_m2: 'Roof area (m²)',
  roof_u_w_m2k: 'Heat transfer through the roof — U-value (W/(m²·K))',
  solar_absorptance: 'Share of sunlight absorbed — absorptance (0–1)',
  capacitance_j_k: 'Heat storage per degree — effective whole-building capacitance (J/K)',
  ventilation_w_k: 'Heat exchange through airflow — ventilation conductance (W/K)',
  internal_gains_w: 'Heat from people and equipment — internal gains (W)',
  exterior_coefficient_w_m2k: 'Heat exchange at the outside roof surface (W/(m²·K))',
  longwave_correction_k: 'Longwave adjustment to the roof boundary temperature (K)'
};
const roofLabels = { metal_sheet: 'Metal sheet', fibre_cement_sheet: 'Fibre-cement sheet', uninsulated_concrete_slab: 'Uninsulated concrete slab', reflective_cool_roof: 'Reflective roof (cool roof)' };
export default function BuildingDetail({ detail, result, onClose }) {
  const dialog = useRef(null);
  useEffect(() => {
    const element = dialog.current;
    const previous = document.activeElement;
    element.showModal();
    return () => { element.close(); previous?.focus(); };
  }, []);
  const { building: b, selection } = detail;
  const base = b.options.find(o => o.option_id === 'baseline');
  const selected = b.options.find(o => o.option_id === selection.option_id);
  const data = base.simulation.indoor_c.map((value, i) => ({ hour: i + 1, baseline: value, selected: selected.simulation.indoor_c[i] }));
  return <dialog ref={dialog} className="detail" aria-labelledby="detail-title" onCancel={e => { e.preventDefault(); onClose(); }}>
    <div className="detail-heading"><div><span className="eyebrow">EXPLORE THIS BUILDING</span><h2 id="detail-title">{b.building_id.replace('demo_', 'Building ')}</h2></div><button onClick={onClose} aria-label="Close building details">Close ×</button></div>
    <p><span className="tag">{optionName(selection.option_id)}</span> · Estimated indoor temperatures from example data; not checked against real buildings</p>
    <aside className="notice" aria-label="How to read these estimates"><strong>A very hot example where the roof has a large effect</strong><span>Large estimated temperature differences depend on assumptions about the roof, airflow, sunlight and how much heat the building stores. The model leaves out walls, windows, floors and changes in ventilation. These results do not show proven cooling effects in real homes.</span></aside>
    {selection.option_id === 'baseline' && <p>No improvement is included for this building. Both lines show the same temperatures.</p>}
    <p id="temperature-chart-help">The lines show estimated indoor temperatures with and without the chosen improvement. The dashed horizontal line is your comparison limit, not a health or safety limit. Each point is the temperature at the end of an hour.</p>
    <div className="chart-heading"><div><span className="eyebrow">TEMPERATURE THROUGH THE WEEK</span><h3>Indoor temperature comparison</h3></div><span className="threshold-chip">Comparison limit: {result.threshold_c} °C</span></div>
    <div className="chart" role="img" aria-describedby="temperature-chart-help" aria-label={`Estimated indoor temperatures without improvements and with ${optionName(selection.option_id)}, by hour from the start; comparison limit ${result.threshold_c} degrees Celsius`}>
      <ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ top: 22, right: 30, bottom: 25, left: 0 }}>
        <CartesianGrid stroke="#e2e9e5" strokeDasharray="3 3" vertical={false}/>
        <XAxis dataKey="hour" minTickGap={30} label={{ value: 'Hours from start', position: 'bottom', offset: 0 }}/>
        <YAxis domain={['auto', 'auto']} width={48} tickFormatter={v => Number(v).toFixed(0)} label={{ value: '°C', angle: -90, position: 'insideLeft' }}/>
        <Tooltip formatter={v => `${Number(v).toFixed(2)} °C`} labelFormatter={h => `Hour ${h} from the start`}/><Legend verticalAlign="top"/>
        <ReferenceLine y={result.threshold_c} stroke="#a86518" strokeWidth={2} strokeDasharray="7 5" label={{ value: `Limit: ${result.threshold_c} °C`, position: 'insideTopRight', fill: '#8b5112', fontSize: 11 }} ifOverflow="extendDomain"/>
        <Line dataKey="baseline" name="Without improvements" stroke="#7c8793" dot={false} strokeWidth={2} strokeDasharray="5 3" isAnimationActive={false}/>
        <Line dataKey="selected" name={selection.option_id === 'baseline' ? 'No improvement planned' : 'With chosen improvement'} stroke="#087d70" dot={false} strokeWidth={3} isAnimationActive={false}/>
      </LineChart></ResponsiveContainer>
    </div>
    <section className="panel allocation-explanation" aria-labelledby="allocation-explanation-title">
      <h3 id="allocation-explanation-title">Understanding this cooling plan</h3>
      <p>HeatShield looks for the mix of improvements that gives the largest total estimated reduction in overheating across all buildings, without going over your budget. Each building can receive at most one improvement.</p>
      <p>The choice that helps this building most may leave less money for other buildings. The citywide plan may therefore choose a different improvement, or none for this building.</p>
      <p>This is a general explanation, not a calculated reason for this building’s choice. We have not calculated how choosing a different improvement here would change the rest of the plan.</p>
    </section>
    <h3>Compare cooling choices</h3>
    <p>Positive values mean less estimated overheating; negative values mean more. K·h adds up heat above your limit over time, not degrees of cooling.</p>
    <div className="table-scroll"><table><thead><tr><th scope="col">Improvement</th><th scope="col">Cost (INR)</th><th scope="col">Change in overheating (K·h)</th></tr></thead><tbody>{b.options.map(o => <tr key={o.option_id}><th scope="row">{optionName(o.option_id)}{o.option_id === selection.option_id ? ' · in this plan' : ''}</th><td>{money(o.cost_minor)}</td><td>{kh(o.signed_avoided_kh)}{o.signed_avoided_kh < 0 && <span className="adverse"> · more overheating</span>}</td></tr>)}</tbody></table></div>
    <details><summary>View hourly temperatures as a table</summary><div className="table-scroll hourly"><table><thead><tr><th>Hour</th><th>Without improvements (°C)</th><th>In this plan (°C)</th></tr></thead><tbody>{data.map(d => <tr key={d.hour}><td>{d.hour}</td><td>{d.baseline.toFixed(2)}</td><td>{d.selected.toFixed(2)}</td></tr>)}</tbody></table></div></details>
    <details className="assumption-details"><summary>Technical details: building inputs and sources</summary>
      <p>This is a Roof-dominated synthetic stress scenario: a simplified model of example buildings, not measurements from actual homes. Technical source notes and all supplied assumptions and limitations are retained below.</p>
      <dl className="parameters">{Object.entries(b.building).map(([k, v]) => <div key={k}><dt>{parameterLabels[k] || k}</dt><dd>{k === 'archetype' ? roofLabels[v] || String(v) : String(v)}</dd></div>)}</dl>
      <p>Data type: {b.source.kind}. Source notes: {b.source.description}</p>
      <ul>{result.assumptions.map(a => <li key={a}>{a}</li>)}</ul><ul>{result.limitations.map(l => <li key={l.code}>{l.text}</li>)}</ul>
    </details>
  </dialog>;
}
