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
  const cards = [['Total budget', money(a.budget_minor), 'Maximum available to spend'], ['Amount spent', money(a.spent_minor), 'Example installation costs'], ['Remaining budget', money(a.remaining_minor), 'Money left in this plan'], ['Estimated reduction in overheating', `${kh(result.summary.signed_avoided_kh)} K·h`, 'Heat above your limit over 7 example days — not degrees of cooling'], ['Buildings with improvements', `${count} / ${result.buildings.length}`, 'No more than one improvement per building']];
  return <section className="summary-block" aria-label="Cooling plan summary">
    <div className="summary">{cards.map(([label, value, note], i) => <div className={`panel stat ${i === 3 ? 'stat-benefit' : ''}`} key={label}><span className="stat-label">{label}</span><strong>{value}</strong><small>{note}</small></div>)}</div>
    <div className="panel allocation-strip">
      <div className="utilization"><div className="indicator-heading"><h3>Budget used</h3><strong>{utilization.toFixed(1)}%</strong></div><div className="utilization-track" role="progressbar" aria-label="Budget used" aria-valuemin={0} aria-valuemax={100} aria-valuenow={utilization} aria-valuetext={a.budget_minor === 0 ? 'No money budgeted' : `${utilization.toFixed(1)} percent of budget spent`}><div style={{ width: `${utilization}%` }}/></div><small>{a.budget_minor === 0 ? 'No money budgeted' : 'Share of your budget used by this plan'}</small></div>
      <div className="distribution"><div className="indicator-heading"><h3>Improvements in this plan</h3><small>{a.selections.length} buildings</small></div><div className="distribution-track" aria-hidden="true">{distribution.map(([id, n]) => <span key={id} className={`segment option-${id}`} style={{ flexGrow: n }}/>)}</div><ul className="distribution-legend" aria-label="Improvements in this plan">{distribution.map(([id, n]) => <li key={id}><span className={`swatch option-${id}`} aria-hidden="true"/>{optionName(id)} <strong>{n}</strong></li>)}</ul></div>
    </div>
  </section>;
}
