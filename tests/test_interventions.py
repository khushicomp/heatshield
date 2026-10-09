import unittest
from dataclasses import replace
from heatshield.contracts import InputKind, Provenance
from heatshield.interventions import CoolRoof, Insulation, Shading
from heatshield.thermal import Archetype, Building, WeatherHour, simulate, overheating_degree_hours

SOURCE = Provenance(InputKind.SYNTHETIC, 'Synthetic test fixture, not physical evidence.')


def building(**changes):
    return replace(Building(Archetype.METAL_SHEET, 40, 5, 0.7, 4e6, 40, 0, 20), **changes)


class InterventionTests(unittest.TestCase):
    def test_cool_roof_changes_only_absorptance_and_label(self):
        b = building()
        weather = (WeatherHour(35, 800),)
        changed, hours = CoolRoof(0.2, SOURCE).apply(b, weather)
        self.assertEqual(replace(changed, archetype=b.archetype, solar_absorptance=b.solar_absorptance), b)
        self.assertIs(hours, weather)
        self.assertLess(simulate(changed, hours, 28).indoor_c[0], simulate(b, weather, 28).indoor_c[0])

    def test_insulation_adds_area_normalized_resistance(self):
        b = building()
        changed, _ = Insulation(1, SOURCE).apply(b, ())
        self.assertAlmostEqual(changed.roof_u_w_m2k, 1 / (1 / 5 + 1))
        self.assertEqual(replace(changed, roof_u_w_m2k=b.roof_u_w_m2k), b)
        zero, _ = Insulation(1, SOURCE).apply(building(roof_u_w_m2k=0), ())
        self.assertEqual(zero.roof_u_w_m2k, 0)

    def test_shading_reduces_solar_only(self):
        b = building()
        weather = (WeatherHour(35, 800), WeatherHour(25, 0))
        changed, hours = Shading(0.6, SOURCE).apply(b, weather)
        self.assertIs(changed, b)
        self.assertEqual(hours, (WeatherHour(35, 320), WeatherHour(25, 0)))
        self.assertEqual(weather[0].solar_w_m2, 800)
        fully_shaded, no_solar = Shading(1, SOURCE).apply(b, weather)
        self.assertTrue(all(h.solar_w_m2 == 0 for h in no_solar))

    def test_zero_strength_is_noop_for_trajectories(self):
        b = building()
        weather = (WeatherHour(35, 800), WeatherHour(25, 0))
        baseline = simulate(b, weather, 28)
        for intervention in (CoolRoof(b.solar_absorptance, SOURCE), Insulation(0, SOURCE), Shading(0, SOURCE)):
            changed, hours = intervention.apply(b, weather)
            self.assertEqual(simulate(changed, hours, 28), baseline)

    def test_insulation_can_increase_overheating(self):
        b = building(ventilation_w_k=0, internal_gains_w=1000, capacitance_j_k=360000)
        hours = (WeatherHour(20, 0),) * 12
        changed, _ = Insulation(1, SOURCE).apply(b, hours)
        base = overheating_degree_hours(simulate(b, hours, 30).indoor_c, 25)
        insulated = overheating_degree_hours(simulate(changed, hours, 30).indoor_c, 25)
        self.assertGreater(insulated, base)

    def test_invalid_interventions(self):
        for factory in (lambda: CoolRoof(-0.1, SOURCE), lambda: CoolRoof(1.1, SOURCE),
                        lambda: Insulation(-1, SOURCE), lambda: Shading(1.1, SOURCE),
                        lambda: Shading(float('nan'), SOURCE), lambda: Insulation(True, SOURCE)):
            with self.assertRaises(ValueError):
                factory()
        with self.assertRaises(ValueError):
            CoolRoof(0.9, SOURCE).apply(building(), ())
        with self.assertRaises(ValueError):
            Insulation(1e308, SOURCE).apply(building(), ())


if __name__ == '__main__':
    unittest.main()
