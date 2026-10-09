"""Synthetic demonstration; no measured weather or calibrated parameters."""
from heatshield import Archetype, Building, WeatherHour, simulate, cool_roof, overheating_degree_hours

baseline = Building(Archetype.METAL_SHEET, roof_area_m2=40, roof_u_w_m2k=5,
                    solar_absorptance=0.7, capacitance_j_k=4e6,
                    ventilation_w_k=40, internal_gains_w=100,
                    exterior_coefficient_w_m2k=20)
weather = [WeatherHour(35, 800)] * 8
for label, building in [('baseline', baseline), ('coating', cool_roof(baseline, 0.2))]:
    result = simulate(building, weather, initial_indoor_c=28)
    print(label, [round(t, 2) for t in result.indoor_c],
          'proxy K.h:', round(overheating_degree_hours(result.indoor_c, 30), 2),
          'hourly Euler stable:', result.hourly_forward_euler_stable)
