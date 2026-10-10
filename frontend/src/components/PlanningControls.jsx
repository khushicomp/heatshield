export default function PlanningControls({ budget, threshold, setBudget, setThreshold, onSubmit, loading }) {
  return <form className="controls panel" onSubmit={onSubmit} aria-busy={loading}>
    <div><span className="eyebrow">PLANNING SCENARIO</span><h2>Put your cooling budget to work</h2><p>Compare interventions across 30 hypothetical buildings over seven synthetic days.</p></div>
    <div className="control-fields">
      <label><span id="budget-label">Municipal budget (INR)</span><input aria-labelledby="budget-label" inputMode="decimal" value={budget} onChange={e => setBudget(e.target.value)} required aria-describedby="budget-help" disabled={loading}/><small id="budget-help">0–10,00,000 · up to 2 decimal places</small></label>
      <label>Overheating threshold (°C)<input type="number" min="15" max="45" step="any" value={threshold} onChange={e => setThreshold(e.target.value)} required disabled={loading}/><small>Comparison threshold, not a health boundary</small></label>
      <button className="primary" type="submit" disabled={loading}>{loading ? 'Running allocation…' : 'Run allocation'}</button>
    </div>
  </form>;
}
