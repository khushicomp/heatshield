# HeatShield — Cooling Where It Counts

**Explore cooling interventions. Allocate a limited budget. See the assumptions.**

[Live dashboard](https://staging.d22u8i6a71q15e.amplifyapp.com/) · [Architecture](docs/ARCHITECTURE.md) · [Algorithm](docs/ALGORITHM.md) · [Verification](docs/VERIFICATION.md)

> **Synthetic scenario — not empirically validated.** The dashboard uses a **Roof-dominated synthetic stress scenario**: 30 hypothetical buildings and seven days of analytic hourly weather. Results are model demonstrations, not predictions for actual households, established cooling effects or public-health outcomes.

## Problem and solution

Municipal cooling budgets are limited, while buildings respond differently to heat and interventions have different costs. HeatShield makes that allocation problem explorable: simulate a baseline and cooling options for each hypothetical building, compare estimated overheating, then choose a budget-feasible allocation.

The working application provides:

- Configurable municipal budget in INR and overheating threshold in °C.
- Baseline, cool-roof, insulation and roof-shading simulations.
- Exact multiple-choice budget optimization for explicitly rounded model scores.
- Spending, remaining budget, intervention distribution and building allocations.
- Building-level hourly temperature comparisons, signed option benefits and physical assumptions.
- A React dashboard on AWS Amplify, connected through API Gateway to Python on AWS Lambda.

There are no dataset uploads, authentication, persistent storage, ML models or arbitrary heat-risk scores. The public API accepts only the synthetic preset, budget and threshold.

## How it works

The single-zone thermal model uses whole-building SI quantities:

```text
C dT/dt = UA(T_sol_air − T) + H_vent(T_out − T) + Q_internal
T_sol_air = T_out + alpha I_roof / h_out − longwave_correction
```

`U` is area-normalized roof transmittance in W/(m²·K); `A` is roof area in m². `UA` and ventilation conductance `H_vent` are in W/K; effective whole-zone capacitance `C` is in J/K; internal gains are in W. Roof resistance is `1/UA` K/W and equivalent parallel-path resistance is `1/(UA + H_vent)`. Absorptance `alpha` is dimensionless, roof-plane irradiance is in W/m², and exterior coefficient `h_out` is in W/(m²·K).

Exact exponential integration advances the linear model under constant forcing within each hour. Outputs are end-of-hour temperatures. Cool roofs reduce absorptance, insulation adds roof resistance, and shading attenuates incident solar; they do not interchange these mechanisms.

Overheating degree-hours are `sum(max(T_end_hour − threshold, 0) × 1 hour)`, in **K·h**. For example, 2 K above the threshold for 3 sampled hours contributes 6 K·h. This accumulated building-overheating proxy is **not degrees Celsius of cooling**, a health-risk measure or a thermal-comfort compliance assessment.

Signed avoided K·h equals baseline minus intervention overheating. Negative values remain visible. Optimization uses `max(0, signed benefit)`, rounded per option to integer micro-K·h with half-even rounding. Sparse exact dynamic programming selects at most one intervention per building within the budget. Ties prefer lower cost, fewer interventions, then lexicographic assignment. There is no hard-coded preference for cool roofs. See [the algorithm](docs/ALGORITHM.md).

Costs are illustrative one-time fixed charges plus a roof-area rate. Decimal arithmetic rounds final charges upward to paise; budgets must be exact paise. The frontend displays backend totals and preserves score strings.

## Architecture and technologies

```text
Browser → Amplify-hosted React/Vite → HTTPS API Gateway → Lambda adapter
    → allocation service → synthetic preset → thermal comparisons → optimizer
    ← versioned JSON: allocations, trajectories, costs, provenance and limitations
```

Python 3.10+ uses only the standard library at runtime. The frontend uses React 19, Vite 6 and Recharts 3; tests use unittest, Vitest, Testing Library and jsdom. Frontend dependencies are locked in `frontend/package-lock.json`. No AWS SDK is needed by the calculation service. See [architecture and API contract](docs/ARCHITECTURE.md).

## Local development

Prerequisites: Python 3.10+ and Node.js 22 or 24 with npm. Run commands from the repository root unless indicated. No Python package installation is required; optional editable installation is `python -m pip install -e .`.

Terminal 1:

```powershell
python -B -m heatshield.api.server
```

Terminal 2:

```powershell
cd frontend
npm ci
# Clear any shell production setting to use the local proxy:
Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
npm run dev
```

Open http://127.0.0.1:5173. Python listens on http://127.0.0.1:8000; Vite proxies `/api` to it. If an ignored local `.env` file sets `VITE_API_BASE_URL`, unset that entry too. Both servers bind to loopback; stop with Ctrl+C.

CLI-only demonstration:

```powershell
python -B -m examples.municipal_demo --budget 75000 --threshold 30
```

Optional JSON export: append `--output outputs/municipal_demo.json`. Generated outputs and local datasets are ignored by Git.

## Tests and production build

```powershell
python -B -m unittest discover -s tests -v
cd frontend
npm test
npm run build
npm run verify:build
```

With Python and Vite running, `npm run verify:local` exercises the actual frontend API client through the proxy and reconciles it against the direct backend. `npm run preview` serves the build at http://127.0.0.1:4173 with the same local API proxy.

The October 11 submission check passed **72 Python tests and 16 frontend tests**. Coverage includes analytical thermal behavior, intervention transformations, adverse benefits, exact money, exhaustive-search comparisons on small optimization cases, deterministic ties, state-limit failure, API validation, Lambda packaging and UI states. Tests establish implementation consistency, **not scientific accuracy**. Component tests mock chart drawing and native dialog methods; manual browser review remains relevant.

The public dashboard was also rehearsed in Chrome with both demo budgets and a real building chart. See [verification evidence and boundaries](docs/VERIFICATION.md).

## Deployment overview

The public dashboard is deployed on Amplify; API Gateway forwards requests to Lambda. `heatshield.api.lambda_handler.handler` accepts HTTP API payload v2 events and delegates to the transport-independent service. This repository does not provision AWS infrastructure automatically.

To prepare artifacts for the existing API, without deploying:

```powershell
cd frontend
$env:VITE_API_BASE_URL = 'https://hdt6pym543.execute-api.ap-southeast-2.amazonaws.com'
npm run build:deploy
cd ..
python -B scripts/package_frontend.py
python -B scripts/package_lambda.py
```

The API origin is public build-time configuration, not a credential. Packaging writes ignored ZIPs under `outputs/` and does not upload or alter AWS resources. Use the Python frontend packager: it verifies portable ZIP paths and avoids the Windows archive-header defect that caused missing Amplify assets.

`amplify.yml` prepares optional GitHub monorepo builds with app root `frontend`, Node 24, tests and asset checks. Its presence does not establish that Git-based deployment is enabled. Preserve the working public origin and CORS configuration. See [deployment and packaging](docs/DEPLOYMENT.md).

Verify published assets without changing AWS:

```powershell
cd frontend
npm run verify:public -- https://staging.d22u8i6a71q15e.amplifyapp.com/
```

## Limitations and future improvements

All preset thermal inputs, weather and costs are author-selected provisional assumptions, not calibrated measurements or market quotations. Large simulated differences depend on roof, ventilation, solar and capacitance assumptions. Walls, windows, floors, variable ventilation, humidity, radiant comfort and physiology are not represented. Archetype names do not establish representative construction properties.

Benefits cover seven synthetic days, while costs are one-time charges. Buildings receive equal weighting; population, vulnerability, equity, maintenance and lifetime effects are absent. Exact optimization applies to supplied rounded scores, not universally optimal real-world policy. The 50,000-candidate-state cap can reject a request rather than return an approximation.

Real-data validation remains paused following [feasibility](docs/research/tasgaonkar_feasibility.md) and [integrity](docs/research/tasgaonkar_integrity.md) investigations. Unresolved clock conventions and household grouping prevent a defensible held-out validation claim. Sensitivity analysis, empirical validation, richer physics and equity-aware objectives are future work, not current features.

[Model assumptions](docs/MODEL_ASSUMPTIONS.md) documents the exact synthetic preset and physical-background references. Those references support concepts, not the demonstration parameters or model accuracy. No measured environmental impact or validation statistics are claimed.
