import math
import unittest
from dataclasses import replace
from heatshield import Archetype, Building, WeatherHour, simulate, cool_roof, overheating_degree_hours


def building(**changes):
    values = dict(archetype=Archetype.METAL_SHEET, roof_area_m2=40,
                  roof_u_w_m2k=5, solar_absorptance=0.7, capacitance_j_k=4e6,
                  ventilation_w_k=40, internal_gains_w=0,
                  exterior_coefficient_w_m2k=20)
    return Building(**(values | changes))


class ThermalTests(unittest.TestCase):
    def test_equilibrium(self):
        result = simulate(building(), [WeatherHour(30, 0)] * 24, 30)
        self.assertEqual(result.indoor_c, (30,) * 24)

    def test_analytical_solution_and_relaxation(self):
        b = building()
        result = simulate(b, [WeatherHour(35, 0)] * 12, 20)
        expected = 35 + (20 - 35) * math.exp(-240 * 12 * 3600 / 4e6)
        self.assertAlmostEqual(result.indoor_c[-1], expected)
        self.assertTrue(all(20 < t < 35 for t in result.indoor_c))

    def test_stiff_system_stays_bounded(self):
        result = simulate(building(capacitance_j_k=1000), [WeatherHour(40, 0)] * 3, 20)
        self.assertFalse(result.hourly_forward_euler_stable)
        self.assertTrue(all(20 <= t <= 40 for t in result.indoor_c))

    def test_euler_boundary(self):
        result = simulate(building(capacitance_j_k=240 * 3600 / 2), [], 20)
        self.assertFalse(result.hourly_forward_euler_stable)

    def test_adiabatic_energy_balance(self):
        result = simulate(building(roof_u_w_m2k=0, ventilation_w_k=0,
                                  internal_gains_w=100, capacitance_j_k=360000),
                          [WeatherHour(50, 800)] * 2, 20)
        self.assertEqual(result.indoor_c, (21, 22))
        self.assertTrue(math.isinf(result.time_constant_hours))

    def test_internal_gains_equilibrium(self):
        self.assertEqual(simulate(building(internal_gains_w=240),
                                  [WeatherHour(30, 0)], 31).indoor_c, (31,))

    def test_area_scaling(self):
        b = building(internal_gains_w=100)
        doubled = replace(b, roof_area_m2=80, capacitance_j_k=8e6,
                          ventilation_w_k=80, internal_gains_w=200)
        weather = [WeatherHour(35, 700)] * 6
        self.assertEqual(simulate(b, weather, 25).indoor_c,
                         simulate(doubled, weather, 25).indoor_c)

    def test_coating_preserves_physics_and_reduces_solar_response(self):
        b = building()
        cool = cool_roof(b, 0.2)
        self.assertEqual(replace(cool, archetype=b.archetype,
                                 solar_absorptance=b.solar_absorptance), b)
        sunny = [WeatherHour(35, 800)] * 8
        baseline = simulate(b, sunny, 25)
        changed = simulate(cool, sunny, 25)
        self.assertTrue(all(c < a for c, a in zip(changed.indoor_c, baseline.indoor_c)))
        self.assertLess(overheating_degree_hours(changed.indoor_c, 30),
                        overheating_degree_hours(baseline.indoor_c, 30))
        night = [WeatherHour(30, 0)] * 3
        self.assertEqual(simulate(b, night, 25).indoor_c, simulate(cool, night, 25).indoor_c)

    def test_sol_air_and_longwave(self):
        result = simulate(building(longwave_correction_k=2), [WeatherHour(30, 800)], 30)
        self.assertEqual(result.sol_air_c, (56,))

    def test_metric(self):
        self.assertEqual(overheating_degree_hours([28, 30, 32, 35], 30), 7)
        self.assertEqual(overheating_degree_hours([], 30), 0)

    def test_archetypes_and_empty_input(self):
        for archetype in Archetype:
            self.assertEqual(simulate(building(archetype=archetype), [], 25).indoor_c, ())

    def test_invalid_inputs(self):
        for changes in ({'capacitance_j_k': 0}, {'solar_absorptance': 1.1},
                        {'ventilation_w_k': -1}, {'roof_u_w_m2k': float('nan')},
                        {'exterior_coefficient_w_m2k': 0}, {'roof_area_m2': -1}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                building(**changes)
        with self.assertRaises(ValueError):
            WeatherHour(30, -1)
        with self.assertRaises(ValueError):
            simulate(building(), [], float('inf'))
        with self.assertRaises(ValueError):
            cool_roof(building(), 0.9)
        with self.assertRaises(ValueError):
            overheating_degree_hours([float('nan')], 30)


if __name__ == '__main__':
    unittest.main()
