import json
import unittest
from dataclasses import replace
from decimal import localcontext
from unittest.mock import patch

from heatshield.contracts import InputKind, Provenance
from heatshield.interventions import CoolRoof, Insulation, Shading
from heatshield.scenarios import (BuildingScenario, CostSpec, Currency, InterventionOption,
                                 WeatherSeries, allocate_portfolio, evaluate_portfolio)
from heatshield.thermal import Archetype, Building, WeatherHour, simulate

SOURCE = Provenance(InputKind.SYNTHETIC, 'Synthetic fixture only.')
CURRENCY = Currency('INR', 2)


def scenario(building_id='a', **changes):
    building = Building(Archetype.METAL_SHEET, 40, 5, 0.7, 4e6, 40, 100, 20)
    weather = WeatherSeries('sun', (WeatherHour(35, 800),) * 8, SOURCE)
    cost = CostSpec(CURRENCY, '1', '0', SOURCE)
    options = (InterventionOption('cool', CoolRoof(0.2, SOURCE), cost),
               InterventionOption('insulation', Insulation(1, SOURCE), cost),
               InterventionOption('shade', Shading(0.6, SOURCE), cost))
    return replace(BuildingScenario(building_id, building, 28, weather, options, SOURCE), **changes)


class ScenarioTests(unittest.TestCase):
    def test_cost_ceiling_and_exact_budget_units(self):
        self.assertEqual(CostSpec(CURRENCY, '0', '0.001', SOURCE).quote_minor(1), 1)
        self.assertEqual(CostSpec(CURRENCY, '1.005', '0', SOURCE).quote_minor(40), 101)
        self.assertEqual(CostSpec(CURRENCY, '0.01', '0.01', SOURCE).quote_minor(0.1), 2)
        self.assertEqual(CostSpec(CURRENCY, '500', '60', SOURCE).quote_minor(40), 290000)
        self.assertEqual(CURRENCY.budget_minor('1.01'), 101)
        with self.assertRaises(ValueError):
            CURRENCY.budget_minor('1.005')

    def test_cost_and_budget_are_independent_of_callers_decimal_precision(self):
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(CURRENCY.budget_minor('1.01'), 101)
            self.assertEqual(CostSpec(CURRENCY, '1.005', '0', SOURCE).quote_minor(40), 101)

    def test_invalid_money_and_currency(self):
        factories = [lambda: CostSpec(CURRENCY, 1.1, '0', SOURCE),
                     lambda: CostSpec(CURRENCY, '-1', '0', SOURCE),
                     lambda: CostSpec(CURRENCY, 'NaN', '0', SOURCE),
                     lambda: CostSpec(CURRENCY, '0.0000001', '0', SOURCE),
                     lambda: Currency('inr'), lambda: Currency('INR', True),
                     lambda: Currency('INR', 7), lambda: CURRENCY.budget_minor('1e13')]
        for factory in factories:
            with self.assertRaises(ValueError):
                factory()

    def test_comparisons_and_baseline_simulated_once(self):
        s = scenario()
        with patch('heatshield.scenarios.simulate', wraps=simulate) as run:
            evaluation = evaluate_portfolio([s], 30, CURRENCY)
            self.assertEqual(run.call_count, 4)
        options = evaluation.buildings[0].options
        self.assertEqual(options[0].option_id, 'baseline')
        self.assertEqual(options[0].cost_minor, 0)
        self.assertEqual(options[0].signed_avoided_kh, 0)
        for option in options[1:]:
            self.assertAlmostEqual(option.signed_avoided_kh, options[0].overheating_kh - option.overheating_kh)
            self.assertEqual(len(option.simulation.indoor_c), 8)
        self.assertEqual(s.building.solar_absorptance, 0.7)
        self.assertEqual(s.weather.hours[0].solar_w_m2, 800)

    def test_adverse_benefit_is_visible_but_not_selected(self):
        s = scenario()
        b = replace(s.building, ventilation_w_k=0, internal_gains_w=1000, capacitance_j_k=360000)
        weather = WeatherSeries('night', (WeatherHour(20, 0),) * 12, SOURCE)
        s = replace(s, building=b, weather=weather, initial_indoor_c=30, options=(s.options[1],))
        evaluation = evaluate_portfolio([s], 25, CURRENCY)
        adverse = evaluation.buildings[0].options[1]
        self.assertLess(adverse.signed_avoided_kh, 0)
        self.assertEqual(adverse.score_units, 0)
        self.assertEqual(adverse.to_dict()['nonnegative_avoided_kh'], 0)
        result = allocate_portfolio(evaluation, 100)
        self.assertEqual(result['allocation']['selections'][0]['option_id'], 'baseline')

    def test_json_has_finite_values_and_safe_score_strings(self):
        s = scenario(options=())
        s = replace(s, building=replace(s.building, roof_u_w_m2k=0, ventilation_w_k=0))
        result = allocate_portfolio(evaluate_portfolio([s], 30, CURRENCY), 0)
        restored = json.loads(json.dumps(result, allow_nan=False))
        simulation = restored['buildings'][0]['options'][0]['simulation']
        self.assertIsNone(simulation['time_constant_hours'])
        self.assertTrue(simulation['time_constant_infinite'])
        self.assertEqual(restored['allocation']['score_units'], '0')
        self.assertEqual(restored['optimization_score']['unit'], 'micro_K.h')
        self.assertEqual(restored['weather'][0]['source']['kind'], 'synthetic')

    def test_budget_boundaries_after_cost_rounding(self):
        s = scenario()
        option = replace(s.options[0], cost=CostSpec(CURRENCY, '1.005', 0, SOURCE))
        evaluation = evaluate_portfolio([replace(s, options=(option,))], 30, CURRENCY)
        self.assertEqual(allocate_portfolio(evaluation, 100)['allocation']['spent_minor'], 0)
        self.assertEqual(allocate_portfolio(evaluation, 101)['allocation']['spent_minor'], 101)
        with self.assertRaises(ValueError):
            allocate_portfolio(evaluation, 2**53)

    def test_portfolio_order_is_deterministic(self):
        a, b = scenario('a'), scenario('b')
        left = allocate_portfolio(evaluate_portfolio([a, b], 30, CURRENCY), 100)
        right = allocate_portfolio(evaluate_portfolio([replace(b, options=tuple(reversed(b.options))), a], 30, CURRENCY), 100)
        self.assertEqual(left, right)

    def test_horizon_start_currency_and_weather_id_consistency(self):
        a, b = scenario('a'), scenario('b')
        mismatches = [replace(b, weather=replace(b.weather, hours=b.weather.hours[:-1])),
                      replace(b, weather=replace(b.weather, interval_start_iso='2026-10-01T00:00:00Z')),
                      replace(b, weather=replace(b.weather, hours=(WeatherHour(36, 800),) * 8))]
        for other in mismatches:
            with self.assertRaises(ValueError):
                evaluate_portfolio([a, other], 30, CURRENCY)
        with self.assertRaises(ValueError):
            evaluate_portfolio([a], 30, Currency('USD'))
        # Different aware representations of the same start are equivalent.
        a = replace(a, weather=replace(a.weather, series_id='a', interval_start_iso='2026-10-01T00:00:00Z'))
        b = replace(b, weather=replace(b.weather, series_id='b', interval_start_iso='2026-10-01T05:30:00+05:30'))
        self.assertEqual(evaluate_portfolio([a, b], 30, CURRENCY).horizon_hours, 8)

    def test_invalid_scenario_contracts(self):
        s = scenario()
        factories = [lambda: replace(s, building_id=' '), lambda: replace(s, initial_indoor_c=float('inf')),
                     lambda: replace(s, options=s.options + (s.options[0],)),
                     lambda: replace(s, options=(replace(s.options[0], intervention=CoolRoof(0.9, SOURCE)),)),
                     lambda: WeatherSeries('empty', (), SOURCE),
                     lambda: replace(s.weather, interval_start_iso='2026-10-01T00:00:00'),
                     lambda: InterventionOption('baseline', Shading(0.5, SOURCE), s.options[0].cost),
                     lambda: Provenance('synthetic', 'fixture'), lambda: Provenance(InputKind.SYNTHETIC, ''),
                     lambda: evaluate_portfolio([s, s], 30, CURRENCY),
                     lambda: evaluate_portfolio([], 30, CURRENCY),
                     lambda: evaluate_portfolio([s], float('nan'), CURRENCY)]
        for factory in factories:
            with self.assertRaises(ValueError):
                factory()

    def test_user_supplied_provenance_is_not_relabelled_as_measured(self):
        source = Provenance(InputKind.USER_SUPPLIED, 'Unvalidated user-entered geometry and assumptions.')
        result = evaluate_portfolio([replace(scenario(), source=source)], 30, CURRENCY).to_dict()
        self.assertEqual(result['buildings'][0]['source']['kind'], 'user_supplied_unvalidated')


if __name__ == '__main__':
    unittest.main()
