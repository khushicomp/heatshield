import { useEffect, useRef } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Legend } from 'recharts';
import { kh, money, optionName } from '../format.js';
const parameterLabels = {
  archetype: 'Roof archetype',
  roof_area_m2: 'Roof area (m²)',
  roof_u_w_m2k: 'Roof U-value (W/(m²·K))',
  solar_absorptance: 'Solar absorptance (dimensionless)',
  capacitance_j_k: 'Effective whole-zone capacitance (J/K)',
  ventilation_w_k: 'Whole-zone ventilation conductance (W/K)',
  internal_gains_w: 'Whole-zone internal gains (W)',
  exterior_coefficient_w_m2k: 'Exterior heat-transfer coefficient (W/(m²·K))',
  longwave_correction_k: 'Sol-air longwave correction (K)'
};
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
    <div className="detail-heading"><div><span className="eyebrow">BUILDING COMPARISON</span><h2 id="detail-title">{b.building_id.replace('demo_', 'Building ')}</h2></div><button onClick={onClose} aria-label="Close building details">Close ×</button></div>
    <p><span className="tag">{optionName(selection.option_id)}</span> · Synthetic, unvalidated indoor temperatures</p>
    <aside className="notice" aria-label="Scenario interpretation"><strong>Roof-dominated synthetic stress scenario</strong><span>Large simulated temperature differences depend on provisional roof, ventilation, solar and capacitance assumptions. Walls, windows, floors and variable ventilation are not represented by this reduced-order model. These differences are not empirically established cooling effects.</span></aside>
    {selection.option_id === 'baseline' && <p>No intervention selected. The selected trajectory equals baseline.</p>}
    <div className="chart-heading"><div><span className="eyebrow">HOURLY THERMAL RESPONSE</span><h3>Indoor temperature comparison</h3></div><span className="threshold-chip">Threshold {result.threshold_c} degrees C</span></div>
    <div className="chart" role="img" aria-label={`Baseline and ${optionName(selection.option_id)} indoor temperature by relative hour, threshold ${result.threshold_c} degrees Celsius`}><ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{ top: 22, right: 30, bottom: 25, left: 0 }}><CartesianGrid stroke="#e2e9e5" strokeDasharray="3 3" vertical={false}/><XAxis dataKey="hour" minTickGap={30} label={{ value: 'Relative hour (end of interval)', position: 'bottom', offset: 0 }}/><YAxis domain={['auto', 'auto']} width={48} tickFormatter={v => Number(v).toFixed(0)} label={{ value: '°C', angle: -90, position: 'insideLeft' }}/><Tooltip formatter={v => `${Number(v).toFixed(2)} °C`} labelFormatter={h => `Hour ${h}`}/><Legend verticalAlign="top"/><ReferenceLine y={result.threshold_c} stroke="#a86518" strokeWidth={2} strokeDasharray="7 5" label={{ value: `Threshold ${result.threshold_c} degrees C`, position: 'insideTopRight', fill: '#8b5112', fontSize: 11 }} ifOverflow="extendDomain"/><Line dataKey="baseline" name="Baseline" stroke="#7c8793" dot={false} strokeWidth={2} strokeDasharray="5 3" isAnimationActive={false}/><Line dataKey="selected" name="Selected option" stroke="#087d70" dot={false} strokeWidth={3} isAnimationActive={false}/></LineChart></ResponsiveContainer></div>
    <h3>Compare all options</h3><div className="table-scroll"><table><thead><tr><th scope="col">Option</th><th scope="col">Cost (INR)</th><th scope="col">Signed avoided K·h</th></tr></thead><tbody>{b.options.map(o => <tr key={o.option_id}><th scope="row">{optionName(o.option_id)}{o.option_id === selection.option_id ? ' · selected' : ''}</th><td>{money(o.cost_minor)}</td><td>{kh(o.signed_avoided_kh)}{o.signed_avoided_kh < 0 && <span className="adverse"> · increases overheating</span>}</td></tr>)}</tbody></table></div>
    <details><summary>Accessible hourly temperature table</summary><div className="table-scroll hourly"><table><thead><tr><th>Hour</th><th>Baseline °C</th><th>Selected °C</th></tr></thead><tbody>{data.map(d => <tr key={d.hour}><td>{d.hour}</td><td>{d.baseline.toFixed(2)}</td><td>{d.selected.toFixed(2)}</td></tr>)}</tbody></table></div></details>
    <details className="assumption-details"><summary>Physical inputs, assumptions and provenance</summary><dl className="parameters">{Object.entries(b.building).map(([k, v]) => <div key={k}><dt>{parameterLabels[k] || k}</dt><dd>{String(v)}</dd></div>)}</dl><p>{b.source.kind}: {b.source.description}</p><ul>{result.assumptions.map(a => <li key={a}>{a}</li>)}</ul><ul>{result.limitations.map(l => <li key={l.code}>{l.text}</li>)}</ul></details>
  </dialog>;
}
