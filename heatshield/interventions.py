"""Pure single-intervention transformations around the unchanged thermal engine."""
from dataclasses import dataclass, replace
from .contracts import Provenance, finite, provenance
from .thermal import Building, WeatherHour, cool_roof


@dataclass(frozen=True)
class CoolRoof:
    absorptance: float
    source: Provenance

    def __post_init__(self):
        finite(self.absorptance, 'absorptance', 0)
        if self.absorptance > 1:
            raise ValueError('absorptance must be <= 1')
        provenance(self.source)

    def apply(self, building: Building, weather: tuple[WeatherHour, ...]):
        return cool_roof(building, self.absorptance), weather

    def to_dict(self):
        return {'kind': 'cool_roof', 'solar_absorptance': self.absorptance, 'source': self.source.to_dict()}


@dataclass(frozen=True)
class Insulation:
    added_resistance_m2k_w: float
    source: Provenance

    def __post_init__(self):
        finite(self.added_resistance_m2k_w, 'added resistance', 0)
        provenance(self.source)

    def apply(self, building: Building, weather: tuple[WeatherHour, ...]):
        # R is area-normalized. Equivalent to 1 / (1/U + R), including U=0.
        product = building.roof_u_w_m2k * self.added_resistance_m2k_w
        finite(product, 'U times added resistance', 0)
        return replace(building, roof_u_w_m2k=building.roof_u_w_m2k / (1 + product)), weather

    def to_dict(self):
        return {'kind': 'insulation', 'added_resistance_m2k_w': self.added_resistance_m2k_w,
                'source': self.source.to_dict()}


@dataclass(frozen=True)
class Shading:
    solar_reduction_fraction: float
    source: Provenance

    def __post_init__(self):
        finite(self.solar_reduction_fraction, 'solar reduction fraction', 0)
        if self.solar_reduction_fraction > 1:
            raise ValueError('solar reduction fraction must be <= 1')
        provenance(self.source)

    def apply(self, building: Building, weather: tuple[WeatherHour, ...]):
        changed = tuple(WeatherHour(h.outdoor_c, h.solar_w_m2 * (1 - self.solar_reduction_fraction))
                        for h in weather)
        return building, changed

    def to_dict(self):
        return {'kind': 'shading', 'solar_reduction_fraction': self.solar_reduction_fraction,
                'source': self.source.to_dict()}


Intervention = CoolRoof | Insulation | Shading
