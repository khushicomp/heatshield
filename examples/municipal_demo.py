"""Reproducible synthetic municipal scenario; no measurements or validation.

python -B -m examples.municipal_demo --budget 75000 --output outputs/municipal_demo.json
Budget is in illustrative INR major units. JSON computation results exclude runtime.
"""
import argparse
import json
from pathlib import Path
from time import perf_counter

from heatshield.presets import CURRENCY, make_scenarios
from heatshield.scenarios import allocate_portfolio, evaluate_portfolio


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
