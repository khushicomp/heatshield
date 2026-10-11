export default function PlanningControls({ budget, threshold, setBudget, setThreshold, onSubmit, loading }) {
  return <form className="controls panel" onSubmit={onSubmit} aria-busy={loading}>
    <div><span className="eyebrow">BUILD YOUR COOLING PLAN</span><h2>Where could your cooling budget help most?</h2><p>Choose how much to spend. HeatShield compares cooling improvements for 30 example buildings over seven made-up hot days.</p></div>
    <div className="control-fields">
      <label><span id="budget-label">Total cooling budget (INR)</span><input aria-labelledby="budget-label" inputMode="decimal" value={budget} onChange={e => setBudget(e.target.value)} required aria-describedby="budget-help" disabled={loading}/><small id="budget-help">Indian rupees: 0–10,00,000. No commas; up to 2 decimal places.</small></label>
      <label><span id="temperature-label">Temperature limit for comparison (°C)</span><input aria-labelledby="temperature-label" aria-describedby="temperature-help" type="number" min="15" max="45" step="any" value={threshold} onChange={e => setThreshold(e.target.value)} required disabled={loading}/><small id="temperature-help">We count indoor heat above this value. Choose 15–45 °C; this is not a health or safety limit.</small></label>
      <button className="primary" type="submit" disabled={loading}>{loading ? 'Creating your plan…' : 'Create cooling plan'}</button>
    </div>
  </form>;
}
