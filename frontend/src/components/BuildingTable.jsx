import { money, kh, optionName } from '../format.js';
export default function BuildingTable({ result, onSelect }) {
  return <section className="panel table-panel"><div className="section-heading"><div><span className="eyebrow">ALLOCATION RESULTS</span><h2>Building-by-building plan</h2></div><span className="pill">{result.horizon_hours} hourly steps · synthetic</span></div>
    <div className="table-scroll"><table><caption className="sr-only">Selected cooling interventions. Open a building for comparison details.</caption><thead><tr><th scope="col">Building</th><th scope="col">Selected intervention</th><th scope="col">Cost (INR)</th><th scope="col">Estimated avoided K·h</th></tr></thead><tbody>{result.allocation.selections.map(s => {
      const b = result.buildings.find(b => b.building_id === s.building_id);
      const o = b.options.find(o => o.option_id === s.option_id);
      return <tr key={s.building_id}><th scope="row"><button className="building-link" onClick={() => onSelect(b, s)} aria-label={`Inspect ${s.building_id}`}>{s.building_id.replace('demo_', 'Building ')} <span aria-hidden="true">↗</span></button></th><td><span className={`tag ${s.option_id === 'baseline' ? 'neutral' : ''}`}>{optionName(s.option_id)}</span></td><td>{money(o.cost_minor)}</td><td>{kh(o.signed_avoided_kh)}</td></tr>;
    })}</tbody></table></div><p className="table-note">Benefits are estimates for this seven-day scenario. Display values are rounded; totals come directly from the backend.</p>
  </section>;
}
