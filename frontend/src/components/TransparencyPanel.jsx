export default function TransparencyPanel({ result }) {
  return <section className="panel transparency"><span className="eyebrow">SCIENTIFIC TRANSPARENCY</span><h2>Understand the estimate</h2><p><strong>K·h means overheating degree-hours.</strong> One hour at 2 °C above the threshold contributes 2 K·h. Avoided K·h compares accumulated exceedance; it is not a temperature reduction in °C or a public-health outcome.</p>
    <p>All buildings, weather and costs are synthetic illustrations. Results depend on provisional thermal and cost assumptions and have not been empirically validated.</p>
    {result && <details><summary>View assumptions, provenance and limitations</summary><h3>Assumptions</h3><ul>{result.assumptions.map(a => <li key={a}>{a}</li>)}</ul><h3>Limitations</h3><ul>{result.limitations.map(l => <li key={l.code}>{l.text}</li>)}</ul><h3>Weather provenance</h3>{result.weather.map(w => <p key={w.series_id}>{w.source.kind}: {w.source.description}</p>)}<p>Exact rounded optimization score: <code>{result.allocation.score_units}</code> micro-K·h. Equal building weighting; no population or vulnerability weighting.</p></details>}
  </section>;
}
