"""Reproducible synthetic municipal scenario; no measurements or validation.

python -B -m examples.municipal_demo --budget 75000 --output outputs/municipal_demo.json
Budget is in illustrative INR major units. JSON computation results exclude runtime.
"""
import argparse
import json
import math
from pathlib import Path
from time import perf_counter

from heatshield.contracts import InputKind, Provenance
from heatshield.interventions import CoolRoof, Insulation, Shading
from heatshield.scenarios import (BuildingScenario, CostSpec, Currency, InterventionOption,
                                 WeatherSeries, allocate_portfolio, evaluate_portfolio)
from heatshield.thermal import Archetype, Building, WeatherHour

CURRENCY = Currency('INR', 2)
PHYSICAL = Provenance(InputKind.SYNTHETIC, 'Author-selected provisional demonstration inputs; no empirical calibration.')
COSTS = Provenance(InputKind.SYNTHETIC, 'Illustrative one-time installed costs in INR; not market quotations.')


def make_scenarios():
    hours = tuple(WeatherHour(34 + 5 * math.sin(2 * math.pi * (hour % 24 - 9) / 24) + (hour // 24) * 0.2,
                              max(0.0, 850 * math.sin(math.pi * (hour % 24 - 6) / 12)))
                  for hour in range(7 * 24))
    weather = WeatherSeries('synthetic_hot_week', hours, PHYSICAL)
    templates = ((Archetype.METAL_SHEET, 5.0, 0.7),
                 (Archetype.FIBRE_CEMENT_SHEET, 3.5, 0.65),
                 (Archetype.UNINSULATED_CONCRETE_SLAB, 2.5, 0.6),
                 (Archetype.COOL_ROOF, 5.0, 0.3))
    options = (InterventionOption('cool_roof', CoolRoof(0.2, PHYSICAL), CostSpec(CURRENCY, '500', '60', COSTS)),
               InterventionOption('insulation', Insulation(1.0, PHYSICAL), CostSpec(CURRENCY, '1500', '180', COSTS)),
               InterventionOption('shading', Shading(0.6, PHYSICAL), CostSpec(CURRENCY, '1000', '100', COSTS)))
    scenarios = []
    for i in range(30):
        archetype, u, alpha = templates[i % len(templates)]
        building = Building(archetype, roof_area_m2=30 + 5 * (i % 7), roof_u_w_m2k=u,
                            solar_absorptance=alpha, capacitance_j_k=2e6 + (i % 6) * 0.8e6,
                            ventilation_w_k=20 + 5 * (i % 5), internal_gains_w=80 + 20 * (i % 4),
                            exterior_coefficient_w_m2k=20, longwave_correction_k=0)
        scenarios.append(BuildingScenario(f'demo_{i+1:02d}', building, 28, weather, options, PHYSICAL))
    return tuple(scenarios)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--budget', default='75000', help='Exact INR major-unit budget; decimal string')
    parser.add_argument('--threshold', type=float, default=30)
    parser.add_argument('--state-limit', type=int, default=50_000)
    parser.add_argument('--output', type=Path, help='Optional JSON file; use ignored outputs/ for generated artifacts')
    args = parser.parse_args()
    started = perf_counter()
    scenarios = make_scenarios()
    evaluation = evaluate_portfolio(scenarios, args.threshold, CURRENCY)
    result = allocate_portfolio(evaluation, CURRENCY.budget_minor(args.budget), state_limit=args.state_limit)
    payload = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    elapsed = perf_counter() - started
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + '\n', encoding='utf-8')
    selected = [c for c in result['allocation']['selections'] if c['option_id'] != 'baseline']
    print('SYNTHETIC DEMONSTRATION: unvalidated scenario estimates, not household predictions or causal effects.')
    print(f'Buildings: {len(scenarios)}; hourly records per building: {evaluation.horizon_hours}')
    print(f"Budget: {result['allocation']['budget_minor']} minor INR units; spent: {result['allocation']['spent_minor']}; remaining: {result['allocation']['remaining_minor']}")
    print(f"Selected interventions: {len(selected)}; avoided overheating proxy: {result['summary']['signed_avoided_kh']:.6f} K.h")
    print(f"Score units: {result['allocation']['score_units']}; peak working states: {result['allocation']['peak_working_states']}")
    print(f'Runtime (construction, simulations, optimization and JSON serialization; excludes disk write): {elapsed:.6f} s')
    if args.output:
        print(f'JSON written to {args.output}')


if __name__ == '__main__':
    main()
