"""Validated portfolio comparisons and JSON contracts; no API or infrastructure."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, localcontext
import math
import re
from typing import Iterable

from .contracts import Provenance, finite, identifier, integer, provenance
from .interventions import CoolRoof, Insulation, Intervention, Shading
from .optimization import Choice, optimize, benefit_score
from .thermal import Building, SimulationResult, WeatherHour, overheating_degree_hours, simulate

MAX_JSON_INTEGER = 2**53 - 1


def _decimal(value) -> Decimal:
    # JSON callers should use decimal strings, not binary floats, for money.
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError('Money amounts/rates require decimal strings, integers or Decimal')
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValueError('Invalid decimal money value') from None
    if (not result.is_finite() or result < 0 or result.adjusted() > 12
            or result.as_tuple().exponent < -6 or len(result.as_tuple().digits) > 36):
        raise ValueError('Money must be nonnegative, finite, < 1e13 and have at most six decimal places')
    return result


@dataclass(frozen=True)
class Currency:
    code: str
    decimal_places: int = 2

    def __post_init__(self):
        if not isinstance(self.code, str) or not re.fullmatch('[A-Z]{3}', self.code):
            raise ValueError('Currency code must contain three uppercase letters')
        integer(self.decimal_places, 'currency decimal places')
        if self.decimal_places > 6:
            raise ValueError('At most six currency decimal places are supported')

    def budget_minor(self, major) -> int:
        with localcontext() as context:
            context.prec = 64
            scaled = _decimal(major) * 10**self.decimal_places
        if scaled != scaled.to_integral_value() or scaled > MAX_JSON_INTEGER:
            raise ValueError('Budget must be an exact number of minor units within JSON-safe integer range')
        return int(scaled)

    def to_dict(self):
        return {'code': self.code, 'decimal_places': self.decimal_places, 'cost_unit': 'minor_currency_unit'}


@dataclass(frozen=True)
class CostSpec:
    currency: Currency
    fixed_major: Decimal | str | int
    per_roof_m2_major: Decimal | str | int
    source: Provenance

    def __post_init__(self):
        if not isinstance(self.currency, Currency):
            raise ValueError('Explicit Currency required')
        provenance(self.source)
        object.__setattr__(self, 'fixed_major', _decimal(self.fixed_major))
        object.__setattr__(self, 'per_roof_m2_major', _decimal(self.per_roof_m2_major))

    def quote_minor(self, roof_area_m2: float) -> int:
        finite(roof_area_m2, 'roof area', 0)
        area = Decimal(str(roof_area_m2))
        with localcontext() as context:
            context.prec = max(80, sum(len(d.as_tuple().digits) + abs(d.as_tuple().exponent)
                                      for d in (area, self.fixed_major, self.per_roof_m2_major)) + 16)
            total = (self.fixed_major + area * self.per_roof_m2_major) * 10**self.currency.decimal_places
            rounded = total.to_integral_value(rounding=ROUND_CEILING)
        if rounded > MAX_JSON_INTEGER:
            raise ValueError('Cost exceeds JSON-safe integer range')
        return int(rounded)

    def to_dict(self):
        return {'fixed_major': str(self.fixed_major), 'per_roof_m2_major': str(self.per_roof_m2_major),
                'rounding': 'ceiling_to_minor_unit_after_fixed_plus_area_rate', 'source': self.source.to_dict()}


@dataclass(frozen=True)
class WeatherSeries:
    series_id: str
    hours: tuple[WeatherHour, ...]
    source: Provenance
    interval_start_iso: str | None = None

    def __post_init__(self):
        identifier(self.series_id)
        provenance(self.source)
        object.__setattr__(self, 'hours', tuple(self.hours))
        if not self.hours or any(not isinstance(h, WeatherHour) for h in self.hours):
            raise ValueError('Nonempty consecutive complete hourly WeatherHour records required')
        for hour in self.hours:
            finite(hour.outdoor_c, 'outdoor temperature')
            finite(hour.solar_w_m2, 'irradiance', 0)
        self.start_utc()

    def start_utc(self):
        if self.interval_start_iso is None:
            return None  # Explicit relative-hour axis, not a guessed timezone.
        if not isinstance(self.interval_start_iso, str):
            raise ValueError('Interval start must be an offset-aware ISO string')
        try:
            stamp = datetime.fromisoformat(self.interval_start_iso.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('Invalid interval-start timestamp') from None
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError('Interval start requires an explicit UTC offset')
        return stamp.astimezone(timezone.utc)

    def to_dict(self):
        return {'series_id': self.series_id, 'source': self.source.to_dict(),
                'interval_start_iso': self.interval_start_iso, 'step_hours': 1,
                'interpretation': 'consecutive hourly constant forcing; outputs at interval ends',
                'hours': [{'outdoor_c': h.outdoor_c, 'solar_w_m2': h.solar_w_m2} for h in self.hours]}


@dataclass(frozen=True)
class InterventionOption:
    option_id: str
    intervention: Intervention
    cost: CostSpec

    def __post_init__(self):
        identifier(self.option_id)
        if self.option_id == 'baseline':
            raise ValueError('baseline is generated internally and reserved')
        if not isinstance(self.intervention, (CoolRoof, Insulation, Shading)) or not isinstance(self.cost, CostSpec):
            raise ValueError('Supported intervention and explicit CostSpec required')


@dataclass(frozen=True)
class BuildingScenario:
    building_id: str
    building: Building
    initial_indoor_c: float
    weather: WeatherSeries
    options: tuple[InterventionOption, ...]
    source: Provenance

    def __post_init__(self):
        identifier(self.building_id)
        provenance(self.source)
        if not isinstance(self.building, Building) or not isinstance(self.weather, WeatherSeries):
            raise ValueError('Building and WeatherSeries required')
        for name, value in asdict(self.building).items():
            if name != 'archetype':
                finite(value, name)
        finite(self.initial_indoor_c, 'initial indoor temperature')
        object.__setattr__(self, 'options', tuple(self.options))
        if any(not isinstance(o, InterventionOption) for o in self.options):
            raise ValueError('InterventionOption inputs required')
        if len({o.option_id for o in self.options}) != len(self.options):
            raise ValueError('Duplicate option IDs within building')
        for option in self.options:
            if isinstance(option.intervention, CoolRoof) and option.intervention.absorptance > self.building.solar_absorptance:
                raise ValueError('Cool roof cannot increase baseline absorptance')


def _simulation_dict(result: SimulationResult):
    return {'initial_indoor_c': result.initial_indoor_c, 'indoor_c': list(result.indoor_c),
            'sol_air_c': list(result.sol_air_c),
            'time_constant_hours': result.time_constant_hours if math.isfinite(result.time_constant_hours) else None,
            'time_constant_infinite': math.isinf(result.time_constant_hours),
            'hourly_forward_euler_stable': result.hourly_forward_euler_stable}


@dataclass(frozen=True)
class OptionEvaluation:
    option: InterventionOption | None
    cost_minor: int
    simulation: SimulationResult
    overheating_kh: float
    signed_avoided_kh: float
    score_units: int

    @property
    def option_id(self):
        return self.option.option_id if self.option is not None else 'baseline'

    def to_dict(self):
        return {'option_id': self.option_id, 'cost_minor': self.cost_minor,
                'cost_spec': self.option.cost.to_dict() if self.option else None,
                'intervention': self.option.intervention.to_dict() if self.option else {'kind': 'baseline'},
                'overheating_kh': self.overheating_kh, 'signed_avoided_kh': self.signed_avoided_kh,
                'nonnegative_avoided_kh': max(0.0, self.signed_avoided_kh),
                'score_units': str(self.score_units), 'simulation': _simulation_dict(self.simulation)}


@dataclass(frozen=True)
class BuildingEvaluation:
    scenario: BuildingScenario
    options: tuple[OptionEvaluation, ...]

    def to_dict(self):
        params = asdict(self.scenario.building)
        params['archetype'] = self.scenario.building.archetype.value
        return {'building_id': self.scenario.building_id, 'building': params,
                'source': self.scenario.source.to_dict(), 'weather_id': self.scenario.weather.series_id,
                'initial_indoor_c': self.scenario.initial_indoor_c,
                'options': [o.to_dict() for o in self.options]}


@dataclass(frozen=True)
class PortfolioEvaluation:
    buildings: tuple[BuildingEvaluation, ...]
    currency: Currency
    threshold_c: float
    horizon_hours: int

    def choices(self):
        return tuple(Choice(b.scenario.building_id, o.option_id, o.cost_minor, o.score_units)
                     for b in self.buildings for o in b.options)

    def to_dict(self):
        weather = {b.scenario.weather.series_id: b.scenario.weather for b in self.buildings}
        return {'schema_version': 'heatshield.phase3a.v1', 'currency': self.currency.to_dict(),
                'threshold_c': self.threshold_c, 'horizon_hours': self.horizon_hours,
                'benefit_unit': 'K.h per building summed without population weighting',
                'optimization_score': {'unit': 'micro_K.h', 'precision_kh': '0.000001',
                                       'rounding': 'ROUND_HALF_EVEN_per_option', 'negative_benefit': 'clamped_to_zero'},
                'metric': 'sum(max(end_of_hour_indoor_c-threshold_c,0))*1_hour',
                'interpretation': 'Unvalidated scenario estimates; not household predictions, health risk or causal effects.',
                'weather': [weather[k].to_dict() for k in sorted(weather)],
                'buildings': [b.to_dict() for b in self.buildings]}


def evaluate_portfolio(scenarios: Iterable[BuildingScenario], threshold_c: float, currency: Currency) -> PortfolioEvaluation:
    finite(threshold_c, 'overheating threshold')
    if not isinstance(currency, Currency):
        raise ValueError('Explicit Currency required')
    scenarios = tuple(scenarios)
    if not scenarios or any(not isinstance(s, BuildingScenario) for s in scenarios):
        raise ValueError('At least one BuildingScenario required')
    if len({s.building_id for s in scenarios}) != len(scenarios):
        raise ValueError('Duplicate building IDs')
    horizons = {(s.weather.start_utc(), len(s.weather.hours)) for s in scenarios}
    if len(horizons) != 1:
        raise ValueError('All buildings require a common evaluation start and horizon')
    weather_ids = {}
    for scenario in scenarios:
        series = scenario.weather
        if series.series_id in weather_ids and weather_ids[series.series_id] != series:
            raise ValueError('Weather ID reused for different inputs/provenance')
        weather_ids[series.series_id] = series
        if any(o.cost.currency != currency for o in scenario.options):
            raise ValueError('Mixed currency or minor-unit definitions are not permitted')
    evaluated = []
    for scenario in sorted(scenarios, key=lambda s: s.building_id):
        base = simulate(scenario.building, scenario.weather.hours, scenario.initial_indoor_c)
        base_kh = overheating_degree_hours(base.indoor_c, threshold_c)
        finite(base_kh, 'baseline degree-hours', 0)
        options = [OptionEvaluation(None, 0, base, base_kh, 0.0, 0)]
        for option in sorted(scenario.options, key=lambda o: o.option_id):
            building, hours = option.intervention.apply(scenario.building, scenario.weather.hours)
            result = simulate(building, hours, scenario.initial_indoor_c)
            kh = overheating_degree_hours(result.indoor_c, threshold_c)
            finite(kh, 'intervention degree-hours', 0)
            signed = base_kh - kh
            options.append(OptionEvaluation(option, option.cost.quote_minor(scenario.building.roof_area_m2),
                                            result, kh, signed, benefit_score(signed)))
        evaluated.append(BuildingEvaluation(scenario, tuple(options)))
    return PortfolioEvaluation(tuple(evaluated), currency, threshold_c, len(scenarios[0].weather.hours))


def allocate_portfolio(evaluation: PortfolioEvaluation, budget_minor: int, *, state_limit: int = 50_000):
    integer(budget_minor, 'budget_minor')
    if budget_minor > MAX_JSON_INTEGER:
        raise ValueError('Budget exceeds JSON-safe integer range')
    allocation = optimize(evaluation.choices(), budget_minor, state_limit=state_limit)
    chosen = {(c.building_id, c.option_id) for c in allocation.selections}
    selected = [o for b in evaluation.buildings for o in b.options
                if (b.scenario.building_id, o.option_id) in chosen]
    summary = {'baseline_overheating_kh': math.fsum(b.options[0].overheating_kh for b in evaluation.buildings),
               'selected_overheating_kh': math.fsum(o.overheating_kh for o in selected),
               'signed_avoided_kh': math.fsum(o.signed_avoided_kh for o in selected),
               'nonnegative_avoided_kh': math.fsum(max(0.0, o.signed_avoided_kh) for o in selected)}
    for name, value in summary.items():
        finite(value, name)
    result = evaluation.to_dict()
    result['allocation'] = allocation.to_dict()
    result['summary'] = summary
    result['solver_settings'] = {'state_limit': state_limit, 'limit_scope': 'candidate distinct costs before pruning',
                                 'tie_break': ['score_desc', 'cost_asc', 'intervention_count_asc', 'assignment_lex_asc']}
    return result
