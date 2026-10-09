"""Exact sparse multiple-choice knapsack for integer costs and benefit scores."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Iterable
from .contracts import finite, identifier, integer

SCORE_SCALE = 1_000_000


def benefit_score(signed_avoided_kh: float) -> int:
    """Clamp adverse benefits to zero; round K.h to micro-K.h, half-even."""
    finite(signed_avoided_kh, 'signed avoided degree-hours')
    with localcontext() as context:
        context.prec = 64
        return int((Decimal(str(max(0.0, signed_avoided_kh))) * SCORE_SCALE).to_integral_value(rounding=ROUND_HALF_EVEN))


class StateLimitExceeded(RuntimeError):
    """No allocation is returned when the declared working-state limit is exceeded."""


@dataclass(frozen=True)
class Choice:
    building_id: str
    option_id: str
    cost_minor: int
    score_units: int

    def __post_init__(self):
        identifier(self.building_id)
        identifier(self.option_id)
        integer(self.cost_minor, 'cost_minor')
        integer(self.score_units, 'score_units')
        if self.option_id == 'baseline' and (self.cost_minor or self.score_units):
            raise ValueError('Baseline must have zero cost and score')

    def to_dict(self):
        return {'building_id': self.building_id, 'option_id': self.option_id,
                'cost_minor': self.cost_minor, 'score_units': str(self.score_units)}


@dataclass(frozen=True)
class Allocation:
    selections: tuple[Choice, ...]
    budget_minor: int
    spent_minor: int
    score_units: int
    peak_working_states: int

    def to_dict(self):
        return {'selections': [c.to_dict() for c in self.selections],
                'budget_minor': self.budget_minor, 'spent_minor': self.spent_minor,
                'remaining_minor': self.budget_minor - self.spent_minor,
                'score_units': str(self.score_units), 'score_precision_kh': '0.000001',
                'score_rounding': 'ROUND_HALF_EVEN_per_option',
                'algorithm': 'exact_sparse_multiple_choice_dynamic_programming',
                'peak_working_states': self.peak_working_states}


@dataclass(frozen=True)
class _State:
    score: int
    count: int
    choices: tuple[Choice, ...]

    @property
    def same_cost_key(self):
        return (-self.score, self.count, tuple((c.building_id, c.option_id) for c in self.choices))


def optimize(choices: Iterable[Choice], budget_minor: int, *, state_limit: int = 50_000) -> Allocation:
    """One option per building, including its mandatory zero-cost baseline.

    Ties: score descending, cost ascending, intervention count ascending, then
    assignment lexicographically. Dominance pruning is exact for these rules.
    The limit bounds distinct candidate costs BEFORE pruning at every stage;
    failure is explicit even if pruning might subsequently shrink that set.
    """
    integer(budget_minor, 'budget_minor')
    integer(state_limit, 'state_limit', 1)
    grouped = {}
    for choice in choices:
        if not isinstance(choice, Choice):
            raise ValueError('Choice inputs required')
        options = grouped.setdefault(choice.building_id, {})
        if choice.option_id in options:
            raise ValueError('Duplicate option ID within building')
        options[choice.option_id] = choice
    if any('baseline' not in group for group in grouped.values()):
        raise ValueError('Every building requires a zero-cost baseline choice')
    states = {0: _State(0, 0, ())}
    peak = 1
    for building_id in sorted(grouped):
        pending = {}
        for spent, state in sorted(states.items()):
            for option_id, choice in sorted(grouped[building_id].items()):
                cost = spent + choice.cost_minor
                if cost > budget_minor:
                    continue
                candidate = _State(state.score + choice.score_units,
                                   state.count + (choice.option_id != 'baseline'),
                                   state.choices + (choice,))
                if cost not in pending or candidate.same_cost_key < pending[cost].same_cost_key:
                    pending[cost] = candidate
                if len(pending) > state_limit:
                    raise StateLimitExceeded(f'Working states exceed {state_limit} at building {building_id}; no result returned')
        peak = max(peak, len(pending))
        states = {}
        best_score = -1
        for cost, state in sorted(pending.items()):
            # An equal-score higher-cost state loses on cost regardless of count.
            if state.score > best_score:
                states[cost] = state
                best_score = state.score
    cost, best = min(states.items(), key=lambda item: (-item[1].score, item[0],
                                                     item[1].count, item[1].same_cost_key[2]))
    return Allocation(best.choices, budget_minor, cost, best.score, peak)
