# Synthetic scenario and physical assumptions

The shared preset in `heatshield/presets.py` is a **Roof-dominated synthetic stress scenario**. All numerical inputs are author-selected provisional illustrations: no measured calibration, product specification, market quotation or uncertainty distribution is claimed. Archetype names do not make the values representative of actual construction.

See [the algorithm](ALGORITHM.md) for the heat balance, exact hourly integration, metric, costs, precision and optimization. See [architecture](ARCHITECTURE.md) for API limits. This document records the numerical scenario and physical interpretation.

## Reproducible inputs

For building index `i=0..29`, IDs are `demo_01` through `demo_30`:

| Input | Rule |
|---|---|
| Roof label / U / absorptance | Cycle metal/5/0.7, fibre-cement/3.5/0.65, uninsulated concrete/2.5/0.6, reflective/5/0.3; U in W/(m²·K) |
| Roof area | `30 + 5*(i mod 7)` m² |
| Effective whole-zone capacitance | `2,000,000 + 800,000*(i mod 6)` J/K |
| Whole-zone ventilation conductance | `20 + 5*(i mod 5)` W/K |
| Whole-zone internal gains | `80 + 20*(i mod 4)` W |
| Exterior coefficient | 20 W/(m²·K) |
| Longwave correction | 0 K |
| Initial indoor temperature | 28 °C |
| Default comparison threshold | 30 °C; configurable, not a health boundary |
| Cool roof | Absorptance 0.2 |
| Insulation | Added resistance 1 m²·K/W |
| Roof shading | Incident solar reduction fraction 0.6 |
| Cool-roof cost | INR 500 fixed + INR 60/m² |
| Insulation cost | INR 1,500 fixed + INR 180/m² |
| Shading cost | INR 1,000 fixed + INR 100/m² |

For relative hour `h=0..167`, `q=h mod 24` and `d=floor(h/24)`:

```text
Outdoor temperature (°C) = 34 + 5*sin(2*pi*(q−9)/24) + 0.2*d
Roof-plane irradiance (W/m²) = max(0, 850*sin(pi*(q−6)/12))
```

This is seven days of analytic weather, not an observed heatwave or climate projection. There is no random sampling, warm-up exclusion or hidden initialization fitting. The relative-hour axis assumes consecutive complete hours; it assigns no civil timezone. Repeated computations are deterministic in the tested environment, without a promise of bit-for-bit equality on every floating-point platform.

## Interpretation of interventions

- Cool roofs change absorbed solar fraction only. Roof U, whole-zone capacitance, ventilation, gains and weather are preserved; increasing absorptance is rejected.
- Insulation adds uniform area-normalized series resistance, with unchanged films and no thermal bridges. `R_added = thickness/conductivity` requires traceable material inputs if used outside this illustration. Capacitance stays unchanged; placement and altered coupling to roof storage are omitted. Insulation can restrict heat rejection and increase overheating.
- Shading is a constant effective attenuation of incident roof-plane irradiance, not a geometric shading calculation. Shade temperature, airflow and longwave effects are omitted. Full-roof installed cost is charged, independent of the attenuation fraction.

Irradiance is incident on the roof plane; horizontal-to-tilted conversion is not implemented. U describes the roof assembly, not material conductivity. C describes coupled zone air, fabric and contents, not roof material heat capacity alone. A zero longwave correction omits night-sky cooling; it does not establish its physical absence.

Large simulated temperature differences depend on provisional roof, ventilation, solar and capacitance assumptions. Walls, windows, floors, variable ventilation, humidity, radiant comfort and physiology are omitted. Equal building weighting ignores population and vulnerability. Seven-day benefits and one-time costs do not establish lifetime value or a real-world intervention ranking.

## Evidence and future work

Tests check numerical consistency, not empirical accuracy. Real-data validation remains paused: [feasibility](research/tasgaonkar_feasibility.md) and [integrity](research/tasgaonkar_integrity.md) reports document unresolved clock and household-grouping evidence. Parameter uncertainty, warm-up choice, independent held-out evaluation and sensitivity analysis still need investigation.

[EnergyPlus material documentation](https://energyplus.readthedocs.io/en/stable/guides/input-output-reference/1.9-group-surface-construction-elements.html) and [outside surface heat balance](https://bigladdersoftware.com/epx/docs/8-7/engineering-reference/outside-surface-heat-balance.html) provide conceptual background. They do not substantiate the numerical preset or validate HeatShield. The fixed-threshold endpoint proxy is not TM52/TM59 compliance or a validated human-health risk measure.
