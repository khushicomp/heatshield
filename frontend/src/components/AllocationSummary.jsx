import { money, kh } from '../format.js';
export default function AllocationSummary({ result }) {
  const a = result.allocation;
  const count = a.selections.filter(s => s.option_id !== 'baseline').length;
  const cards = [['Total budget', money(a.budget_minor)], ['Amount spent', money(a.spent_minor)], ['Remaining budget', money(a.remaining_minor)], ['Estimated avoided overheating', `${kh(result.summary.signed_avoided_kh)} K·h`], ['Buildings receiving interventions', `${count} / ${result.buildings.length}`]];
  return <section className="summary" aria-label="Allocation summary">{cards.map(([label, value]) => <div className="panel stat" key={label}><span>{label}</span><strong>{value}</strong></div>)}</section>;
}
