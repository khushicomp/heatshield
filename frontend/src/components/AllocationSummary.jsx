import { money, kh, optionName } from '../format.js';
export default function AllocationSummary({ result }) {
  const a = result.allocation;
  const count = a.selections.filter(s => s.option_id !== 'baseline').length;
  // Display indicators only; authoritative costs and benefits remain API values.
  const utilization = a.budget_minor > 0 ? a.spent_minor / a.budget_minor * 100 : 0;
  const distribution = Object.entries(a.selections.reduce((counts, s) => {
    counts[s.option_id] = (counts[s.option_id] || 0) + 1;
    return counts;
  }, {})).sort(([left], [right]) => left.localeCompare(right));
  const cards = [['Total budget', money(a.budget_minor), 'Municipal allocation ceiling'], ['Amount spent', money(a.spent_minor), 'Illustrative installed cost'], ['Remaining budget', money(a.remaining_minor), 'Available after allocation'], ['Estimated avoided overheating', `${kh(result.summary.signed_avoided_kh)} K·h`, 'Across the synthetic seven-day period'], ['Buildings receiving interventions', `${count} / ${result.buildings.length}`, 'At most one intervention per building']];
  return <section className="summary-block" aria-label="Allocation summary">
    <div className="summary">{cards.map(([label, value, note], i) => <div className={`panel stat ${i === 3 ? 'stat-benefit' : ''}`} key={label}><span className="stat-label">{label}</span><strong>{value}</strong><small>{note}</small></div>)}</div>
    <div className="panel allocation-strip">
      <div className="utilization"><div className="indicator-heading"><h3>Budget utilization</h3><strong>{utilization.toFixed(1)}%</strong></div><div className="utilization-track" role="progressbar" aria-label="Budget utilization" aria-valuemin={0} aria-valuemax={100} aria-valuenow={utilization} aria-valuetext={a.budget_minor === 0 ? 'No budget allocated' : `${utilization.toFixed(1)} percent of budget spent`}><div style={{ width: `${utilization}%` }}/></div><small>{a.budget_minor === 0 ? 'No budget allocated' : 'Share of the submitted budget used by this allocation'}</small></div>
      <div className="distribution"><div className="indicator-heading"><h3>Intervention distribution</h3><small>{a.selections.length} buildings</small></div><div className="distribution-track" aria-hidden="true">{distribution.map(([id, n]) => <span key={id} className={`segment option-${id}`} style={{ flexGrow: n }}/>)}</div><ul className="distribution-legend" aria-label="Intervention distribution">{distribution.map(([id, n]) => <li key={id}><span className={`swatch option-${id}`} aria-hidden="true"/>{optionName(id)} <strong>{n}</strong></li>)}</ul></div>
    </div>
  </section>;
}
