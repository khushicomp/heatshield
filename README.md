# HeatShield — Cooling Where It Counts

Dependency-free Python 3.10+ thermal archetype engine, with Phase 3A municipal
intervention scenarios and budget optimization. The Phase 1 engine is unchanged.
These are model demonstrations, not digital twins, validated indoor-temperature
predictions, established intervention effects, or human-health risk estimates.

## Run locally

Phase 4 adds a local Python API and React dashboard. See
[Phase 4 startup and API contract](docs/phase4.md) for the two-terminal workflow,
frontend build, request limits and verification commands. The scientific core
remains dependency-free; frontend dependencies are isolated under `frontend/`.

From the repository root:

```powershell
python -m unittest discover -s tests -v
python -m examples.demo
```

Optional installation: `python -m pip install -e .`. Runtime uses only the standard
library, has no filesystem/network side effects, and can be packaged for a later
Lambda handler. A local frontend/API now exists; no cloud resources, database,
authentication or ML is included.

## Model and units

```text
C dT/dt = UA (T_sol_air - T) + H_vent (T_out - T) + Q_internal
T_sol_air = T_out + alpha I_roof / h_out - longwave_correction
```

The ventilation and gain terms are interpreted as additions: warmer outdoor air
and positive internal heat generation warm the zone. Temperatures are Celsius;
differences are kelvin. Time is seconds internally.

- Roof U: W/(m² K), area-normalized transmittance through the complete roof assembly,
  including consistent surface resistance assumptions; not material conductivity.
- Roof area A: m². UA: W/K, whole-building roof conductance.
- Ventilation H: W/K, whole-building sensible exchange conductance, not an air-change
  rate or a surface convection coefficient. Q: whole-building watts (nonnegative).
- C: J/K, whole-building effective thermal capacitance of the coupled air, fabric
  and contents. It is not roof material heat capacity alone. If a capacitance is
  given per floor area, multiply by floor area, not automatically roof area.
- R_roof = 1/UA and equivalent R = 1/(UA+H), K/W. Parallel roof and ventilation
  paths share one thermal storage node; tau = RC seconds. Zero total conductance
  has infinite R/tau and follows C dT/dt = Q.
- Alpha: dimensionless absorbed solar fraction [0,1]. I: W/m² incident on the roof
  plane, not automatically horizontal weather irradiance for a tilted roof.
- h_out: W/(m² K), effective exterior coefficient for the simplified sol-air model.
  Longwave correction: K, positive values cool the effective boundary.

A coating changes alpha only. `cool_roof` preserves U, C, area and other inputs.
Metal, fibre-cement, uninsulated concrete and reflective roof labels are supported;
labels do not secretly select physical constants. A reflective roof needs an
explicit substrate U and effective zone C. Material alone cannot determine them.

## Numerical and reporting conventions

Each weather record represents one consecutive complete hour, held constant during
that hour. `simulate` returns N end-of-hour temperatures and retains the initial
state separately. Missing/irregular records must be handled by the caller; there
is no implicit interpolation or timestamp inference. Gains and ventilation are
constant for a run. Empty weather produces an empty temperature series.

The exact exponential update solves each hourly linear ODE. `expm1` avoids loss of
precision for small steps. It is stable for positive C and nonnegative conductance;
finite-value checks reject invalid inputs or unrepresentable results. The result
also reports tau and whether hourly forward Euler satisfies dt*(UA+H)/C < 2.
Exact integration removes Euler instability, not uncertainty from hourly weather
aggregation or the model structure.

The standardized project metric is sum(max(T_end_hour - threshold, 0) * 1 hour),
in K·h (numerically equivalent to °C·h). Supply the threshold explicitly. It is a
building-overheating proxy using endpoint samples, not an exact integral of the
continuous trajectory, a human-health risk measure, or TM52/TM59 compliance. No
0–100 score is assigned. Initial temperature is not an extra hour of exposure.

## Provisional demonstration inputs and uncertainty

There are deliberately no authoritative archetype parameter presets. Every value
below comes from an **author-selected synthetic demonstration**, with no measured
or literature-derived calibration and no inferred uncertainty distribution:

| Input | Demo value | Unresolved uncertainty |
|---|---:|---|
| Roof area | 40 m² | Geometry unspecified |
| Roof U | 5 W/(m² K) | Assembly, thickness and surface films unspecified |
| Baseline/coating alpha | 0.7 / 0.2 | Product, weathering, dirt and spectrum unspecified |
| Effective zone C | 4,000,000 J/K | Coupled fabric, contents and time scale unknown |
| Ventilation H | 40 W/K | Wind, openings and occupant schedules unknown |
| Internal Q | 100 W | Occupancy and equipment schedules unknown |
| Exterior h | 20 W/(m² K) | Wind/exposure dependence omitted |
| Longwave correction | 0 K | Night-sky cooling omitted, not assumed physically absent |
| Initial T / proxy threshold | 28 / 30 °C | Initialization arbitrary; threshold not a health boundary |
| Weather | 8 hours at 35 °C, 800 W/m² | Synthetic constant forcing, not observations |

Tests use synthetic inputs too. Their numerical values are test fixtures, not
physical parameter evidence. No confidence interval or credible range is claimed.
Users should replace these inputs with traceable assembly, weather and occupancy
information and conduct sensitivity analysis before interpreting scenario effects.

## Sources and scope

The EnergyPlus [outside surface heat balance engineering reference](https://bigladdersoftware.com/epx/docs/23-2/engineering-reference/outside-surface-heat-balance.html)
describes absorbed solar, exterior convection and longwave exchange, and the use
of sol-air temperature to simplify these processes. It supports the physical
concepts, **not the numerical demonstration inputs or validation of this engine**.
[CIBSE TM52](https://www.cibse.org/knowledge-research/knowledge-portal/tm52-the-limits-of-thermal-comfort-avoiding-overheating-in-european-buildings/)
is a distinct overheating assessment framework; this fixed-threshold air-temperature
proxy does not implement it. The exact ODE solution and Euler stability condition
follow directly from this model's linear heat balance.

Unresolved assumptions include the one-node approximation and instantaneous roof
response; omitted wall, window, ground and direct glazing solar exchanges; constant
ventilation and gains; effective C and roof U identification; simplified longwave
and exterior films; initialization/warm-up; roof-plane weather; and occupancy.
Humidity, radiant temperature, air speed, comfort and physiology are absent.
Measured indoor/outdoor data, independent held-out evaluation, parameter estimation
and uncertainty analysis would be required for scientific validation. Tests check
implementation and physical consistency only. Further development phases require separate approval.


## Phase 3A: synthetic municipal scenarios

Compare baseline, cool-roof, insulation and shading options, then allocate an
explicit budget using exact sparse dynamic programming for rounded benefit scores.
Inputs and costs require provenance; synthetic results are not validated household
predictions, health risk estimates or established intervention effects. Real-data
validation remains paused. Phase 3B sensitivity analysis is not implemented.

```powershell
python -B -m examples.municipal_demo --budget 75000 --output outputs/municipal_demo.json
```

The reproducible demo uses 30 hypothetical buildings and 168 hours of analytic
weather. The budget is in illustrative INR major units. See [Phase 3A documentation](docs/phase3a.md)
for contracts, physical/cost assumptions, precision, tie-breaking, solver limits,
actual verification results and limitations. Generated outputs stay out of Git.

## Synthetic stress-scenario interpretation

The municipal preset is a **Roof-dominated synthetic stress scenario**. Large
simulated temperature differences depend on provisional roof, ventilation, solar
and effective-capacitance assumptions. Walls, windows, floors and variable
ventilation are not represented by this reduced-order model. The preset is not
representative housing evidence or an empirically established intervention effect.
This transparency update preserves every numerical input, equation, trajectory,
cost and optimization result; it does not tune temperatures or add model physics.
