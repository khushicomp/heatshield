"""Bounded JSON allocation service, independent of HTTP and cloud providers."""
import json
from heatshield.presets import CURRENCY, make_scenarios
from heatshield.scenarios import evaluate_portfolio, allocate_portfolio
from heatshield.optimization import StateLimitExceeded

PRESET_ID = 'synthetic_municipal_v1'
MAX_BODY_BYTES = 4096
MAX_BUDGET = 100_000_000
STATE_LIMIT = 50_000


def error(status, code, message, fields=None):
    return status, {'error': {'code': code, 'message': message, 'fields': fields or {}}}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON keys')
        result[key] = value
    return result


def _constant(value):
    raise ValueError('Nonstandard JSON number')


def handle_json(body: bytes):
    if len(body) > MAX_BODY_BYTES:
        return error(413, 'REQUEST_TOO_LARGE', 'Maximum request size is 4096 bytes.')
    try:
        request = json.loads(body.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError):
        return error(400, 'INVALID_JSON', 'Expected valid UTF-8 JSON with unique keys and finite numbers.')
    return allocate_request(request)


def allocate_request(request):
    """Return (status, JSON-compatible payload); suitable for a future Lambda adapter."""
    if type(request) is not dict:
        return error(422, 'VALIDATION_ERROR', 'Expected an object.')
    fields = {}
    expected = {'preset_id', 'budget_minor', 'threshold_c'}
    if set(request) != expected:
        fields['request'] = 'Exactly preset_id, budget_minor and threshold_c are required.'
    if request.get('preset_id') != PRESET_ID:
        fields['preset_id'] = f'Only {PRESET_ID} is supported.'
    budget = request.get('budget_minor')
    if type(budget) is not int or not 0 <= budget <= MAX_BUDGET:
        fields['budget_minor'] = f'Must be an integer from 0 to {MAX_BUDGET} paise.'
    threshold = request.get('threshold_c')
    if type(threshold) not in (int, float) or not 15 <= threshold <= 45:
        fields['threshold_c'] = 'Must be a finite number from 15 to 45 degrees Celsius.'
    if fields:
        return error(422, 'VALIDATION_ERROR', 'Request validation failed.', fields)
    try:
        scenarios = make_scenarios()
        if not 1 <= len(scenarios) <= 50 or any(
            not 1 <= len(s.weather.hours) <= 168 or len(s.options) > 3 for s in scenarios
        ):
            raise ValueError('Preset exceeds server limits')
        evaluation = evaluate_portfolio(scenarios, threshold, CURRENCY)
        result = allocate_portfolio(evaluation, budget, state_limit=STATE_LIMIT)
        # Preserve the Phase 3A shape and all option trajectories. Compact JSON on
        # transport avoids pretty-print overhead; allocation contains references,
        # never second copies of trajectories.
        result.update({
            'preset_id': PRESET_ID,
            'units': {'temperature': 'degC', 'time': 'hour', 'money': 'INR paise',
                      'overheating': 'K.h', 'solar': 'W/m2'},
            'assumptions': [
                '30 hypothetical buildings; seven analytic days; initial indoor temperature 28 degC.',
                'All thermal inputs and one-time installed costs are author-selected provisional illustrations.',
                'Cool roof changes absorptance; insulation adds resistance with unchanged capacitance; shading attenuates incident solar.',
                'Hourly forcing is constant within each hour; outputs are end-of-hour samples.'
            ],
            'limitations': [
                {'code': 'UNVALIDATED', 'text': 'Synthetic scenario, not empirically validated household predictions or established causal effects.'},
                {'code': 'PROXY', 'text': 'K.h accumulates temperature exceedance above a threshold over time; it is not degrees Celsius of cooling or a public-health outcome.'},
                {'code': 'UNCERTAINTY', 'text': 'Ventilation, capacitance, gains, solar exposure and costs are uncertain; sensitivity analysis is not included.'},
                {'code': 'ALLOCATION', 'text': 'Exact for rounded supplied scores only. Equal building weighting; no population, equity, maintenance or lifetime benefit model.'}
            ]
        })
        json.dumps(result, allow_nan=False, separators=(',', ':'))
        return 200, result
    except StateLimitExceeded:
        return error(422, 'OPTIMIZATION_STATE_LIMIT', 'Optimizer state limit exceeded; no allocation was returned.')
    except Exception:
        return error(500, 'INTERNAL_ERROR', 'Allocation could not be completed; no allocation was returned.')
