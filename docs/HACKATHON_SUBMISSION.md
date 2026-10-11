# HeatShield — Cooling Where It Counts

## Short pitch

HeatShield explores how a municipality could allocate a limited cooling budget across hypothetical buildings. Transparent thermal simulation compares interventions; exact budget-constrained optimization turns estimated avoided overheating into an inspectable allocation.

## Problem statement

A constrained cooling budget requires choices between buildings and interventions. A useful planning demonstration should explain estimated benefits and the assumptions behind its priorities, rather than hide them behind an unexplained risk score.

## Proposed solution and demonstrated functionality

The public dashboard accepts an INR budget and overheating threshold, allocates interventions across 30 hypothetical buildings, and shows spending, distribution and building-level temperature comparisons. It evaluates cool roofs, insulation and shading against baseline over seven days of hourly synthetic weather.

Each building receives at most one intervention; total cost cannot exceed budget. Costs, signed benefits, physical inputs and caveats remain inspectable. The frontend makes real backend requests; allocations are not hard-coded.

## Technical implementation

- **Scientific core:** dependency-free Python single-zone 1R1C model, with exact exponential integration under hourly constant forcing.
- **Interventions:** cool roofs reduce absorptance; insulation adds roof resistance; shading attenuates roof-plane solar irradiance.
- **Objective:** maximize nonnegative estimated avoided overheating, rounded per option to integer micro-K·h, under an integer-paise budget.
- **Algorithm:** sparse exact multiple-choice knapsack DP with dominance pruning, deterministic ties and explicit state-limit failure.
- **Frontend:** React, Vite and Recharts; exact decimal money conversion, backend totals, comparison charts and accessible detail tables.
- **API:** bounded `POST /api/allocations`, returning versioned strict JSON with trajectories, allocation, units, provenance and limitations. The service is independent of local HTTP and Lambda adapters.

## AWS services used

| Service | Role |
|---|---|
| AWS Amplify Hosting | Public production frontend and HTTPS hosting |
| Amazon API Gateway | HTTPS allocation endpoint and Lambda integration |
| AWS Lambda | Python allocation API, thermal comparisons and optimization |

No database, authentication or uploads are required. Private AWS settings were not independently audited during submission preparation; suggested configuration is not evidence of deployed settings.

## Innovation and differentiation

HeatShield connects physically distinct intervention mechanisms with explicit budget constraints, without arbitrary risk scores. Allocations can be inspected down to individual costs, signed benefits and hourly trajectories. Exact optimization, deterministic precision rules and prominent provenance make the demonstration reproducible and auditable. These are implementation characteristics, not a claim of research novelty or superiority to other tools.

## Potential impact and limitations

The intended value is helping stakeholders explore tradeoffs and identify evidence needed before allocating real cooling funds. **No measured environmental, health or economic impact is established.** K·h is a building-overheating proxy, not a health outcome or degrees Celsius of cooling.

The default is a **Roof-dominated synthetic stress scenario**, not representative housing evidence. Weather, thermal inputs and costs are provisional. Large temperature differences depend on those assumptions. Walls, windows, floors, variable ventilation, humidity, radiant comfort and physiology are omitted. Benefits span seven days; costs are not a lifetime economic model. Population, equity and uncertainty are absent from the objective.

Investigation of published measurements identified unresolved timestamp and household-grouping issues; real-data validation remains paused. Tests verify implementation consistency, not predictive accuracy. Sensitivity analysis, empirical validation and richer objectives are future work.

## Quality evidence

The October 11 submission check passed 72 Python tests and 16 frontend tests; production build and public HTML/JavaScript/CSS checks passed. Tests cover thermal consistency, transformations, money boundaries, exhaustive-search comparisons, determinism, API limits, packaging and UI states. See [README](../README.md) for commands and [architecture](ARCHITECTURE.md) for evidence boundaries.

A public Chrome rehearsal completed both demo budgets and rendered Building 01's chart. [Verification record](VERIFICATION.md) distinguishes these smoke checks from scientific validation and a full browser/accessibility audit.

## Submission links

- **Live demo:** https://staging.d22u8i6a71q15e.amplifyapp.com/
- **GitHub:** https://github.com/khushicomp/heatshield
- **Video:** **TODO — replace with the final publicly viewable demo-video URL.**
- **Demo narration:** [2–3-minute recording script](DEMO_SCRIPT.md)

## Final manual checklist

- Record/upload the demo and verify playback and viewing permissions.
- Replace the video placeholder before copying this draft into the official form.
- Confirm judges have repository access; do not assume a private repository is accessible.
- Check official required fields, eligibility and deadline, then submit. This draft does not submit automatically.
- Recheck the public dashboard before submission. This documentation work requires no AWS redeployment.
