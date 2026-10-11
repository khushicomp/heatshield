import { money, kh, optionName } from '../format.js';
export default function BuildingTable({ result, onSelect }) {
  return <section className="panel table-panel"><div className="section-heading"><div><span className="eyebrow">YOUR COOLING PLAN</span><h2>Building-by-building plan</h2></div><span className="pill">{result.horizon_hours} hours · example data</span></div>
    <div className="table-scroll"><table><caption className="sr-only">Planned cooling improvements. Open a building to compare choices.</caption><thead><tr><th scope="col">Building</th><th scope="col">Chosen improvement</th><th scope="col">Cost (INR)</th><th scope="col">Less overheating (K·h)</th></tr></thead><tbody>{result.allocation.selections.map(s => {
      const b = result.buildings.find(b => b.building_id === s.building_id);
      const o = b.options.find(o => o.option_id === s.option_id);
      return <tr key={s.building_id}><th scope="row"><button className="building-link" onClick={() => onSelect(b, s)} aria-label={`View ${s.building_id.replace('demo_', 'Building ')} details`}>{s.building_id.replace('demo_', 'Building ')} <span aria-hidden="true">↗</span></button></th><td><span className={`tag option-${s.option_id} ${s.option_id === 'baseline' ? 'neutral' : ''}`}>{optionName(s.option_id)}</span></td><td className="numeric">{money(o.cost_minor)}</td><td className="numeric benefit-cell">{kh(o.signed_avoided_kh)}</td></tr>;
    })}</tbody></table></div><p className="table-note">Select a building to compare improvements and estimated indoor temperatures. K·h adds up heat above your temperature limit over time; it is not degrees of cooling. Values shown are rounded; totals come from the calculation service.</p>
  </section>;
}
