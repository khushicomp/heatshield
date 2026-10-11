import { useState } from 'react';
import { requestAllocation } from './api.js';
import { toPaise } from './format.js';
import PlanningControls from './components/PlanningControls.jsx';
import AllocationSummary from './components/AllocationSummary.jsx';
import BuildingTable from './components/BuildingTable.jsx';
import BuildingDetail from './components/BuildingDetail.jsx';
import TransparencyPanel from './components/TransparencyPanel.jsx';
export default function App() {
  const [budget, setBudget] = useState('75000');
  const [threshold, setThreshold] = useState('30');
  const [result, setResult] = useState(null);
  const [submitted, setSubmitted] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [detail, setDetail] = useState(null);
  const stale = result && (submitted.budget !== budget || submitted.threshold !== threshold);
  async function run(event) {
    event.preventDefault(); setError('');
    try {
      const minor = toPaise(budget);
      const degrees = Number(threshold);
      if (!threshold.trim() || !Number.isFinite(degrees) || degrees < 15 || degrees > 45) throw new Error('Choose a temperature limit between 15 and 45 °C.');
      setLoading(true); setDetail(null);
      const response = await requestAllocation(minor, degrees);
      setResult(response); setSubmitted({ budget, threshold });
    } catch (e) { setError(e.message || 'We could not create your cooling plan. Please try again.'); }
    finally { setLoading(false); }
  }
  return <><header className="site-header"><div className="brand-mark" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none"><path d="M20 5 32 10v10c0 7-7 12-12 15C15 32 8 27 8 20V10L20 5Z" stroke="currentColor" strokeWidth="2"/><path d="M14 21c3-7 6 7 12 0M14 16c3-7 6 7 12 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg></div><div><h1>HeatShield<span className="brand-dot" aria-hidden="true">.</span></h1><p>Cooling Where It Counts</p></div><span className="header-label"><span className="status-dot" aria-hidden="true"/> COOLING BUDGET PLANNER</span></header>
    <main><div className="notice"><strong>Example building data — results have not been checked against real buildings</strong><span>This made-up (synthetic) example tests very hot conditions where the roof has a large effect. The estimates are not predictions for actual homes.</span></div>
      <PlanningControls {...{ budget, threshold, setBudget, setThreshold, loading }} onSubmit={run}/>
      {error && <div role="alert" className="error">{error}{result && ' Your previous cooling plan is still shown below.'}</div>}
      {loading && <p role="status">Comparing cooling improvements and finding a plan within your budget…</p>}
      {result ? <><p className="result-context" role="status">{stale ? 'Settings changed — create a new plan to update these results. ' : ''}Plan shown: INR {submitted.budget} budget, {result.threshold_c} °C temperature limit.</p><AllocationSummary result={result}/><BuildingTable result={result} onSelect={(building, selection) => setDetail({ building, selection })}/></> : !loading && <section className="panel empty"><h2>See what your cooling budget could cover</h2><p>Enter a budget and temperature limit, then choose Create cooling plan. We will compare reflective roofs, roof insulation and roof shading.</p><span>30 example buildings · 7 days of hourly estimates · 3 types of improvement</span></section>}
      <TransparencyPanel result={result}/>
    </main><footer>HeatShield · An example tool for exploring cooling choices · No real household data</footer>
    {detail && <BuildingDetail detail={detail} result={result} onClose={() => setDetail(null)}/>}
  </>;
}
