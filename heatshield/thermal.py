"""Whole-building SI heat balance; exact integration of hourly constant forcing."""
from dataclasses import dataclass, replace
from enum import Enum
import math
from typing import Iterable


class Archetype(str, Enum):
    METAL_SHEET = "metal_sheet"
    FIBRE_CEMENT_SHEET = "fibre_cement_sheet"
    UNINSULATED_CONCRETE_SLAB = "uninsulated_concrete_slab"
    COOL_ROOF = "reflective_cool_roof"


def _finite(name: str, value: float, minimum: float | None = None) -> None:
    if not math.isfinite(value) or (minimum is not None and value < minimum):
        raise ValueError(f"{name} must be finite" + (f" and >= {minimum}" if minimum is not None else ""))


@dataclass(frozen=True)
class Building:
    """All values supplied by caller; no calibrated archetype defaults.

    C includes coupled fabric/furnishings, not merely roof or zone air.
    Ventilation is whole-zone W/K; internal gains are whole-zone W.
    """
    archetype: Archetype
    roof_area_m2: float
    roof_u_w_m2k: float
    solar_absorptance: float
    capacitance_j_k: float
    ventilation_w_k: float
    internal_gains_w: float
    exterior_coefficient_w_m2k: float
    longwave_correction_k: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.archetype, Archetype):
            raise ValueError("archetype must be an Archetype")
        for name in ("roof_area_m2", "capacitance_j_k", "exterior_coefficient_w_m2k"):
            value = getattr(self, name)
            _finite(name, value, 0)
            if value == 0:
                raise ValueError(f"{name} must be positive")
        for name in ("roof_u_w_m2k", "ventilation_w_k", "internal_gains_w", "solar_absorptance"):
            _finite(name, getattr(self, name), 0)
        if self.solar_absorptance > 1:
            raise ValueError("solar_absorptance must be <= 1")
        _finite("longwave_correction_k", self.longwave_correction_k)

    @property
    def roof_conductance_w_k(self) -> float:
        return self.roof_area_m2 * self.roof_u_w_m2k


@dataclass(frozen=True)
class WeatherHour:
    """One complete hour; irradiance is incident on the roof plane, W/m²."""
    outdoor_c: float
    solar_w_m2: float

    def __post_init__(self) -> None:
        _finite("outdoor_c", self.outdoor_c)
        _finite("solar_w_m2", self.solar_w_m2, 0)


@dataclass(frozen=True)
class SimulationResult:
    """N end-of-hour temperatures; initial state is separately retained."""
    initial_indoor_c: float
    indoor_c: tuple[float, ...]
    sol_air_c: tuple[float, ...]
    time_constant_hours: float
    hourly_forward_euler_stable: bool


def simulate(building: Building, weather: Iterable[WeatherHour], initial_indoor_c: float) -> SimulationResult:
    """Exact solution per hour, assuming constant weather/gains each hour.

    C dT/dt = UA(T_sol - T) + H_vent(T_out - T) + Q.
    Euler diagnostic uses dt*(UA+H)/C < 2 (strict asymptotic stability).
    """
    _finite("initial_indoor_c", initial_indoor_c)
    ua = building.roof_conductance_w_k
    conductance = ua + building.ventilation_w_k
    _finite("total conductance", conductance, 0)
    ratio = conductance * (3600.0 / building.capacitance_j_k)
    temperatures, sol_air = [], []
    temperature = initial_indoor_c
    for hour in weather:
        sol = hour.outdoor_c + building.solar_absorptance * hour.solar_w_m2 / building.exterior_coefficient_w_m2k - building.longwave_correction_k
        # Net input at the current state avoids cancellation in near-adiabatic cases.
        net_w = ua * (sol - temperature) + building.ventilation_w_k * (hour.outdoor_c - temperature) + building.internal_gains_w
        factor = -math.expm1(-ratio) / conductance if conductance else 3600.0 / building.capacitance_j_k
        temperature += net_w * factor
        _finite("sol-air temperature", sol)
        _finite("computed indoor temperature", temperature)
        temperatures.append(temperature)
        sol_air.append(sol)
    tau = building.capacitance_j_k / conductance / 3600.0 if conductance else math.inf
    return SimulationResult(initial_indoor_c, tuple(temperatures), tuple(sol_air), tau, ratio < 2)


def cool_roof(building: Building, solar_absorptance: float) -> Building:
    """Coating-only scenario: preserves U, C, ventilation and all other inputs."""
    if solar_absorptance > building.solar_absorptance:
        raise ValueError("cool-roof absorptance must not exceed baseline")
    return replace(building, archetype=Archetype.COOL_ROOF, solar_absorptance=solar_absorptance)


def overheating_degree_hours(indoor_c: Iterable[float], threshold_c: float) -> float:
    """Sum max(T_end_of_hour - threshold, 0) * 1 h, in K·h.

    Standardized project convention: building-overheating proxy, not health risk,
    continuous trajectory integration, or a claim of TM52/TM59 compliance.
    """
    _finite("threshold_c", threshold_c)
    total = 0.0
    for temperature in indoor_c:
        _finite("indoor temperature", temperature)
        total += max(temperature - threshold_c, 0.0)
    return total
