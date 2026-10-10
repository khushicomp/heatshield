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
      if (!threshold.trim() || !Number.isFinite(degrees) || degrees < 15 || degrees > 45) throw new Error('Threshold must be between 15 and 45 °C.');
      setLoading(true); setDetail(null);
      const response = await requestAllocation(minor, degrees);
      setResult(response); setSubmitted({ budget, threshold });
    } catch (e) { setError(e.message || 'Unable to connect to the local API.'); }
    finally { setLoading(false); }
  }
  return <><header className="site-header"><div className="brand-mark" aria-hidden="true">H</div><div><h1>HeatShield</h1><p>Cooling Where It Counts</p></div><span className="header-label">MUNICIPAL PLANNING LAB</span></header>
    <main><div className="notice"><strong>Synthetic scenario — not empirically validated</strong><span>Roof-dominated synthetic stress scenario</span><span>Explore provisional cooling allocations. These are not predictions for actual households.</span></div>
      <PlanningControls {...{ budget, threshold, setBudget, setThreshold, loading }} onSubmit={run}/>
      {error && <div role="alert" className="error">{error}{result && ' The previous successful result remains below.'}</div>}
      {loading && <p role="status">Simulating baseline and cooling options, then allocating your budget…</p>}
      {result ? <><p className="result-context" role="status">{stale ? 'Controls changed — run again to update. ' : ''}Showing submitted scenario: INR {submitted.budget}, threshold {result.threshold_c} °C.</p><AllocationSummary result={result}/><BuildingTable result={result} onSelect={(building, selection) => setDetail({ building, selection })}/></> : !loading && <section className="panel empty"><h2>A clearer view of cooling choices</h2><p>Set your budget and run an allocation to compare cool roofs, insulation and shading.</p><span>30 buildings · 168 hours · 3 intervention options</span></section>}
      <TransparencyPanel result={result}/>
    </main><footer>HeatShield · Environmental decision-support demonstration · No real household data</footer>
    {detail && <BuildingDetail detail={detail} result={result} onClose={() => setDetail(null)}/>}
  </>;
}
