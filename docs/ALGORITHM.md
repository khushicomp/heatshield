# Thermal comparisons and budget optimization

Implementation: `heatshield/thermal.py`, `interventions.py`, `scenarios.py` and `optimization.py`. This is an unvalidated archetype simulation and exact optimization of rounded scores, not a demonstrated optimal allocation for real buildings.

## Thermal model and benefits

```text
T_sol = T_out + alpha × I_roof / h_out − longwave_correction
C × dT/dt = UA × (T_sol − T) + H × (T_out − T) + Q
G = UA + H
F_n = UA × (T_sol,n − T_n) + H × (T_out,n − T_n) + Q
T_(n+1) = T_n + F_n × [-expm1(−G × 3600 / C)] / G    if G > 0
T_(n+1) = T_n + Q × 3600 / C                         if G = 0
```

`C` is whole-zone J/K, `UA` and `H` are W/K, and `Q` is W. `U` is W/(m²·K), `A` is m², irradiance is W/m² and `h_out` is W/(m²·K). Temperature differences are kelvin. The exact update assumes a linear one-node model, constant parameters and piecewise-constant hourly forcing. `expm1` improves small-exponent precision. The diagnostic `3600G/C < 2` reports hourly forward-Euler stability; Euler is not used.

The metric is `D = sum(max(T_end_hour − threshold, 0) × 1 hour)` in K·h. This uses endpoint samples, not exact threshold-crossing integration. Initial temperature is not another exposure hour. Each option shares its baseline's initial state and horizon.

| Option | Transformation |
|---|---|
| Baseline | No intervention; zero cost and avoided benefit |
| Cool roof | Reduce `alpha`; preserve U and all other physical inputs |
| Insulation | `U_new = U_old / (1 + U_old × R_added)`; R in m²·K/W; C unchanged |
| Shading | `I_new = (1 − fraction) × I`; building and outdoor temperature unchanged |

Signed benefit `b_ij = D_i,baseline − D_ij` can be negative and remains visible. Objective score `v_ij` is `max(0, b_ij)` rounded per option with `Decimal(str(value))`, scaling by 1,000,000 and `ROUND_HALF_EVEN`. Integer micro-K·h scores serialize as strings. Rounding error is at most half a micro-K·h relative to that decimal input, separate from simulation uncertainty. The unrounded summary need not equal the integer objective divided by a million.

## Costs and formulation

One-time cost is `fixed_INR + roof_area_m2 × rate_INR_per_m2`, with explicit provenance. Decimal arithmetic rounds the final charge **up** to paise. A budget must be exact paise and is never rounded upward. Interventions cover the full roof; shading fraction does not discount charged area.

For binary `x_ij`, with a baseline option for every building:

```text
maximize    sum_i sum_j v_ij × x_ij
subject to  sum_i sum_j c_ij × x_ij ≤ B
            sum_j x_ij = 1  for every building i
            x_ij ∈ {0, 1}
```

The free zero-benefit baseline makes this **at most one nonbaseline intervention per building**. There are no bundles or interactions. Free positive-benefit choices are allowed. Budget may remain unspent.

## Sparse exact dynamic programming

Process sorted building and option IDs, starting from zero cost and score. For each building:

1. Extend retained states with each option; discard costs over budget.
2. At each exact total cost keep the best score, then fewest interventions, then lexicographically smallest assignment.
3. Enforce the distinct candidate-cost limit **before pruning**. Exceeding it raises `StateLimitExceeded`, with no partial allocation or greedy fallback.
4. Sort by cost and discard states whose score is no greater than a cheaper state's score.

Final ties prefer highest score, lowest cost, fewest nonbaseline interventions, then lexicographically smallest complete `(building_id, option_id)` assignment. Cheaper equal-score states dominate regardless of intervention count because cost has higher tie priority. No intervention type receives special treatment.

Sparse DP avoids an array indexed by every paise and is exact for quantized scores when it completes. Greedy benefit/cost ranking can fail; tests include a counterexample and comparisons with exhaustive enumeration. Exhaustive search over four choices for 30 buildings is unsuitable for this demo.

## Complexity and limits

Let `N` be buildings, `K` maximum options including baseline and `S` maximum retained/candidate states. Ignoring assignment bookkeeping, transitions are `O(NKS)` and sorting adds `O(NS log S)`. The implementation copies assignment tuples and constructs comparison keys of length up to N; a conservative bound includes `O(N²KS)` bookkeeping and `O(NS)` stored assignment entries.

State count depends on distinct achievable costs and is bounded by integer budget plus one. The worst case is pseudo-polynomial, not polynomial in the encoded budget length. The public service caps candidate states at 50,000; it can fail even when the subsequent pruned frontier would be small.

Thermal work is `O(NKH)` for H weather hours; the preset evaluates 30 × four options × 168 hours. Retained chart trajectories make response size scale with `NKH`.

## Interpretation and verification

Tests cover physical transformations, adverse outcomes, money boundaries, deterministic ties, budget feasibility, one-choice constraints, JSON, state exhaustion and exhaustive-search agreement. These verify software behavior, not physical accuracy.

The preset favors cool roofs under author-selected costs and roof-dominated assumptions; that is a scenario result, not an empirical ranking. Walls, windows, floors and variable ventilation are omitted. Costs are one-time while benefits span seven days. Population, equity, uncertainty, maintenance and lifetime effects are absent. Real-data validation and sensitivity analysis remain future work.
