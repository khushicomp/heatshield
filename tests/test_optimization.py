import itertools
import random
import unittest
from decimal import localcontext
from heatshield.optimization import Choice, StateLimitExceeded, benefit_score, optimize


def baseline(building_id):
    return Choice(building_id, 'baseline', 0, 0)


def exhaustive(choices, budget):
    groups = {}
    for choice in choices:
        groups.setdefault(choice.building_id, []).append(choice)
    feasible = []
    for assignment in itertools.product(*(groups[key] for key in sorted(groups))):
        spent = sum(c.cost_minor for c in assignment)
        if spent <= budget:
            score = sum(c.score_units for c in assignment)
            count = sum(c.option_id != 'baseline' for c in assignment)
            path = tuple((c.building_id, c.option_id) for c in assignment)
            feasible.append(((-score, spent, count, path), assignment))
    return min(feasible, key=lambda item: item[0])[1]


class OptimizationTests(unittest.TestCase):
    def test_score_clamp_and_half_even_precision(self):
        self.assertEqual(benefit_score(-3), 0)
        self.assertEqual(benefit_score(0.0000005), 0)
        self.assertEqual(benefit_score(0.0000015), 2)
        self.assertEqual(benefit_score(1.2345678), 1234568)
        with self.assertRaises(ValueError):
            benefit_score(float('inf'))

    def test_score_is_independent_of_callers_decimal_precision(self):
        expected = benefit_score(12.1234567)
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(benefit_score(12.1234567), expected)

    def test_exact_budget_and_at_most_one_intervention(self):
        choices = [baseline('a'), Choice('a', 'cool', 6, 10), Choice('a', 'shade', 5, 9),
                   baseline('b'), Choice('b', 'cool', 4, 8)]
        result = optimize(choices, 10)
        self.assertEqual(result.spent_minor, 10)
        self.assertEqual(result.score_units, 18)
        self.assertEqual(len({c.building_id for c in result.selections}), 2)
        self.assertEqual(len(result.selections), 2)
        self.assertLessEqual(result.spent_minor, result.budget_minor)

    def test_zero_budget_still_allows_free_positive_option(self):
        choices = [baseline('a'), Choice('a', 'free', 0, 2), baseline('b'), Choice('b', 'paid', 1, 10)]
        result = optimize(choices, 0)
        self.assertEqual([(c.building_id, c.option_id) for c in result.selections], [('a', 'free'), ('b', 'baseline')])

    def test_ties_prefer_cost_then_count_then_assignment(self):
        choices = [baseline('a'), Choice('a', 'cheap', 4, 10), Choice('a', 'dear', 5, 10)]
        self.assertEqual(optimize(choices, 5).selections[0].option_id, 'cheap')
        choices = [baseline('a'), Choice('a', 'all', 4, 10), Choice('a', 'half', 2, 5),
                   baseline('b'), Choice('b', 'half', 2, 5)]
        result = optimize(choices, 4)
        self.assertEqual([c.option_id for c in result.selections], ['all', 'baseline'])
        tied = [baseline('a'), Choice('a', 'z', 1, 5), Choice('a', 'a', 1, 5)]
        self.assertEqual(optimize(tied, 1).selections[0].option_id, 'a')
        self.assertEqual(optimize([baseline('a'), Choice('a', 'zero', 0, 0)], 0).selections[0].option_id, 'baseline')

    def test_matches_exhaustive_search_and_is_input_order_independent(self):
        rng = random.Random(73)
        for _ in range(60):
            choices = [c for i in range(4) for c in
                       (baseline(str(i)), Choice(str(i), 'x', rng.randrange(8), rng.randrange(12)),
                        Choice(str(i), 'y', rng.randrange(8), rng.randrange(12)))]
            budget = rng.randrange(16)
            expected = exhaustive(choices, budget)
            result = optimize(choices, budget)
            self.assertEqual(result.selections, expected)
            rng.shuffle(choices)
            self.assertEqual(optimize(choices, budget), result)

    def test_greedy_ratio_can_fail(self):
        choices = [baseline('a'), Choice('a', 'x', 6, 12), baseline('b'), Choice('b', 'x', 5, 9),
                   baseline('c'), Choice('c', 'x', 5, 9)]
        result = optimize(choices, 10)
        self.assertEqual(result.score_units, 18)

    def test_state_limit_fails_without_partial_result(self):
        choices = [baseline('a'), Choice('a', 'x', 1, 1)]
        with self.assertRaises(StateLimitExceeded):
            optimize(choices, 1, state_limit=1)

    def test_empty_input_and_invalid_contracts(self):
        self.assertEqual(optimize([], 10).spent_minor, 0)
        factories = [lambda: Choice('a', 'x', -1, 1), lambda: Choice('a', 'x', 1, -1),
                     lambda: Choice('a', 'baseline', 1, 0), lambda: optimize([], True),
                     lambda: optimize([], 1.0), lambda: optimize([], 1, state_limit=0),
                     lambda: optimize([Choice('a', 'x', 1, 1)], 1),
                     lambda: optimize([baseline('a'), baseline('a')], 1)]
        for factory in factories:
            with self.assertRaises(ValueError):
                factory()


if __name__ == '__main__':
    unittest.main()
