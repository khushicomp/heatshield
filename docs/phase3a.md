# Phase 3A: municipal intervention scenarios

This is an **unvalidated synthetic decision-support demonstration**. It does not predict an actual household, establish intervention effectiveness, estimate human-health risk or recommend a real municipal allocation. Phase 2 data limitations remain unresolved. Phase 3B sensitivity analysis is not implemented.

## Run

Python 3.10+; standard-library runtime; no new dependencies.

```powershell
python -B -m unittest discover -s tests -v
python -B -m examples.municipal_demo --budget 75000 --threshold 30 --output outputs/municipal_demo.json
```

`--budget` is a decimal string in INR major units for this demo. Change `--state-limit` to set the optimizer's working-state cap (default 50,000). Generated JSON belongs in ignored `outputs/`; do not commit user-supplied building data without a separate privacy review. Omitting `--output` prints the concise demo result without writing an artifact.

## Architecture and contracts

| Module | Responsibility |
|---|---|
| `heatshield/contracts.py` | Explicit synthetic/user-supplied provenance and shared validation |
| `heatshield/interventions.py` | Pure CoolRoof, Insulation and Shading transformations |
| `heatshield/scenarios.py` | WeatherSeries, BuildingScenario, InterventionOption, Currency and CostSpec; comparisons and JSON output |
| `heatshield/optimization.py` | Independent integer-score multiple-choice knapsack; no thermal or weather dependency |
| `examples/municipal_demo.py` | Deterministic synthetic construction, CLI and optional JSON export |

`heatshield/thermal.py`, Phase 1 tests and all Phase 2 research artifacts are unchanged. Import the new contracts from their modules; existing top-level package exports remain compatible.

Data flow: explicit buildings/weather/options -> evaluate_portfolio -> baseline plus intervention trajectories -> signed benefits/costs/scores -> allocate_portfolio -> JSON-compatible dictionary. Baseline is simulated once per building. Every option uses the same initial state and evaluation horizon as its baseline. There are no intervention combinations.

Each input has `Provenance(InputKind.SYNTHETIC, description)` or `InputKind.USER_SUPPLIED` (serialized as `user_supplied_unvalidated`). User entry is not evidence of measurement or validation. Building parameters retain Phase 1 SI units. IDs must be unique in their scope and cannot have boundary whitespace. The option ID `baseline` is reserved and generated internally.

Weather records are ordered, consecutive complete hours of constant forcing. Empty series, wrong record types and nonfinite values are rejected. An optional ISO interval start must have an explicit UTC offset. All portfolio buildings must share a start instant and horizon length; all-relative series use hour zero without assuming a civil timezone. Weather IDs cannot refer to different records or provenance. Arrays contain no per-record timestamps: callers must establish continuity before constructing them. The contract cannot detect historical gaps hidden by omitted records. Different buildings may have different weather series over the common horizon. There is one threshold per portfolio.

## Physical transformations

- **Cool roof:** lower solar absorptance only, using the existing cool_roof helper. U, C, ventilation, gains and weather are preserved. The archetype label changes to cool roof. Higher-than-baseline absorptance is rejected.
- **Insulation:** supply added area-normalized resistance R_add in m2 K/W. U_new = U_old / (1 + U_old R_add), equivalent to 1/(1/U_old + R_add). U=0 remains zero. This assumes a uniform added resistance, unchanged surface films and no thermal bridges. If using material properties externally, R_add = thickness_m / conductivity_W_mK; both quantities need traceable evidence or an explicit provisional label. No material presets are invented. C remains unchanged: altered thermal coupling, insulation placement and roof-layer storage are omitted. Insulation can worsen overheating by restricting heat rejection; negative results are retained.
- **Shading:** I_new = (1 - solar_reduction_fraction) I, with a constant fraction in [0,1]. This is effective incident roof-plane solar attenuation, not a geometric shaded-area calculation. U, C and outdoor temperature remain unchanged. Longwave exchange, shade temperature and airflow effects are omitted.

Zero-strength changes preserve trajectories. All interventions apply to the full modelled roof; costs are charged using its full area, not multiplied by shading fraction. Roof-plane irradiance is required; no horizontal-to-tilted conversion is implemented.

These mechanisms follow simple series thermal resistance and exterior heat-balance reasoning. [EnergyPlus material documentation](https://energyplus.readthedocs.io/en/stable/guides/input-output-reference/1.9-group-surface-construction-elements.html) and [outside heat balance](https://bigladdersoftware.com/epx/docs/8-7/engineering-reference/outside-surface-heat-balance.html) provide conceptual background, not evidence for the demo's numerical parameters or this engine's accuracy.

## Benefits and costs

The unchanged metric is sum(max(end_of_hour_T - threshold, 0) * 1 hour), in K.h. It is endpoint sampled, not continuous-trajectory integration. Every evaluation returns baseline and intervention trajectories, degree-hours, signed avoided K.h and max(0, signed avoided K.h). Adverse outcomes remain visible; no arbitrary 0-100 risk score is created.

CostSpec uses one-time installed cost = fixed_major + roof_area_m2 * per_roof_m2_major. Prices require explicit provenance. Use decimal strings, integers or Decimal; binary floats for prices are rejected. Rates/charges must be finite, nonnegative, less than 1e13 major units and have at most six decimal places. These are software limits, not market assumptions.

Currency declares its code and number of decimal places (0-6); this is not an exchange-rate service or validation of a currency registry. Mixed codes or decimal-place definitions are rejected. Quote calculation uses decimal arithmetic and rounds the final charge UP to the minor unit. The budget must be an exact number of minor units and is never rounded upward. Portfolio costs and budget must fit integers up to 2^53-1 for JavaScript interoperability. Prices/rates serialize as decimal strings. Precision-sensitive calculations use local decimal contexts rather than inheriting the caller's precision.

The benefit horizon is the supplied weather period, while cost is one-time. Benefits are not annualized or lifetime savings. Maintenance, tax, discounts, contractor capacity, eligibility beyond supplied options and inter-building interactions are absent.

## Optimization and precision

For each building i and option j, choose binary x_ij maximizing sum(v_ij x_ij), with sum(c_ij x_ij) <= budget and exactly one option per building. Each building has a free baseline with zero benefit; consequently there is at most one nonbaseline intervention per building. A budget need not be fully spent. Free positive-benefit options are allowed.

v_ij is max(0, signed avoided K.h) rounded per option to **0.000001 K.h**, using Decimal(str(value)) and ROUND_HALF_EVEN. Integer micro-K.h scores remove tolerance-dependent ties. Quantization can suppress extremely small benefits or change near-ties; exact optimality is for these supplied rounded scores, not the unrounded objective, uncertain physics or real buildings. A per-option rounding error is at most half a micro-K.h relative to the reported decimal value; numerical simulation uncertainty is separate.

Sparse dynamic programming processes sorted building IDs and sorted option IDs. At each exact cost it retains the best score/count/assignment. It then removes higher-cost states with no greater score. These dominance rules preserve the declared objective and tie order:

1. Highest integer benefit score.
2. Lowest total cost.
3. Fewest nonbaseline interventions.
4. Lexicographically smallest complete (building_id, option_id) assignment.

The working-state limit applies to distinct candidate costs BEFORE dominance pruning. It can therefore fail even if a later pruned frontier would be small. `StateLimitExceeded` returns no partial allocation; there is no truncation, greedy fallback or approximate result. Successful runs are exact for the integer scores. State growth is data dependent; peak_working_states is reported. The solver is pseudo-polynomial in the integer-budget bound in the worst case and can still grow substantially for finely differentiated costs. The direct optimizer expects already comparable costs/scores; the portfolio layer enforces common units, threshold and horizon.

## JSON output for later consumers

`allocate_portfolio(...)` returns a plain dictionary with schema_version `heatshield.phase3a.v1`:

- `currency`, threshold, horizon, metric and interpretation.
- Unique weather series, original building parameters and input provenance.
- Every baseline/option trajectory, assumption, cost and signed/nonnegative benefit.
- `allocation`: one selection per building (including baseline), spending, remaining budget, integer score and peak working states.
- `summary`: unrounded baseline/selected degree-hours and avoided benefits.
- `solver_settings`: state limit and tie order.

Score integers serialize as strings to preserve exact values in JavaScript. Infinite time constants serialize as null with an explicit boolean flag; `json.dumps(result, allow_nan=False)` succeeds. End-of-hour array index zero is hour 1; initial state is separate. Results contain no timing or random metadata, allowing repeated computations to serialize identically. CLI runtime is printed separately. Numeric reproducibility is verified in the current Python environment, not promised bit-for-bit across every floating-point platform.

React can later read these contracts for comparisons and allocations. A future Lambda handler can construct contracts, call the same functions and serialize the result. No JSON request parser, API, frontend, cloud resource or deployment is included here. Full trajectories can make outputs large; later transport design should consider response size and privacy. Package discovery already includes the new heatshield modules.

## Synthetic demonstration assumptions

All numerical values below are author-selected provisional illustrations, with no measured calibration, product specification, market quote or uncertainty distribution. The four archetype labels do not make these values representative of actual construction.

For building index i=0..29:

| Input | Explicit rule |
|---|---|
| Roof label / U / absorptance | Cycle metal/5/0.7, fibre-cement/3.5/0.65, uninsulated concrete/2.5/0.6, reflective/5/0.3; U in W/(m2 K) |
| Roof area | 30 + 5*(i mod 7) m2 |
| Effective zone C | 2,000,000 + 800,000*(i mod 6) J/K; whole-zone, not roof material capacity |
| Ventilation | 20 + 5*(i mod 5) W/K |
| Internal gains | 80 + 20*(i mod 4) W |
| Exterior coefficient / longwave correction | 20 W/(m2 K) / 0 K |
| Initial temperature / threshold | 28 / 30 degrees Celsius |
| Cool roof / insulation / shading | absorptance 0.2 / R_add 1 m2 K/W / solar reduction 0.6 |
| Cool-roof cost | INR 500 fixed + INR 60/m2 |
| Insulation cost | INR 1,500 fixed + INR 180/m2 |
| Shading cost | INR 1,000 fixed + INR 100/m2 |

For relative hour h=0..167, q=h mod 24 and d=floor(h/24):

- Outdoor Celsius: 34 + 5*sin(2*pi*(q-9)/24) + 0.2*d.
- Roof-plane irradiance W/m2: max(0, 850*sin(pi*(q-6)/12)).

This seven-day analytic weather is not an observed heatwave or a climate projection. There is no random sampling, warm-up exclusion or hidden initialization fitting.

## Actual verification record

On Python 3.13, Windows, the complete suite passed **57 tests** (0.084 s): 31 existing tests and 26 Phase 3A tests. Coverage includes physical changes, no-op trajectories, adverse insulation, signed/clamped benefits, decimal cost/budget boundaries, valid JSON including infinite tau, provenance, input/horizon/currency checks, all tie levels, explicit state-limit failure, and deterministic outputs. Sixty seeded small portfolios matched exhaustive enumeration exactly, including selected assignments; input shuffling preserved results. This is engineering verification, not scientific validation.

The default demo (INR 75,000 budget) completed in **0.072774 s**, measuring construction, simulations, optimization and JSON serialization, excluding disk writing. It evaluated 30 buildings x 4 options x 168 hours. Results:

- Selected: 24 cool roofs, 6 baselines; other options were evaluated but not selected.
- Spent INR 74,700; remaining INR 300.
- Estimated avoided overheating proxy: 19,380.22421365878 K.h over the synthetic horizon.
- Rounded objective: 19,380,224,213 integer micro-K.h units; peak candidate states: 553.
- Pretty JSON artifact: 1,514,276 bytes. Recomputed JSON was byte-identical, with budget, unique selections and all trajectory lengths checked.

Runtime is an observation from this local run, not a deployment benchmark or SLA. No accuracy, causal effect or municipal policy effectiveness is established by these figures. Unknown ventilation, capacitance, gains, exterior conditions, shading physics, costs and initial states can change rankings. Buildings are weighted equally regardless of size, population or vulnerability; equity is not modelled. Sensitivity analysis is deferred to separately approved Phase 3B.

## Synthetic stress-scenario interpretation

The municipal preset is a **Roof-dominated synthetic stress scenario**. Large
simulated temperature differences depend on provisional roof, ventilation, solar
and effective-capacitance assumptions. Walls, windows, floors and variable
ventilation are not represented by this reduced-order model. The preset is not
representative housing evidence or an empirically established intervention effect.
This transparency update preserves every numerical input, equation, trajectory,
cost and optimization result; it does not tune temperatures or add model physics.
