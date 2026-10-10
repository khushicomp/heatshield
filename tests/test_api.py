import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from heatshield.api.allocations import allocate_request, handle_json, PRESET_ID
from heatshield.api.server import Handler
from heatshield.optimization import StateLimitExceeded
from heatshield.presets import make_scenarios


def request(**changes):
    return {'preset_id': PRESET_ID, 'budget_minor': 7_500_000, 'threshold_c': 30, **changes}


class ApiTests(unittest.TestCase):
    def test_success_reconciles_and_serializes(self):
        status, result = allocate_request(request())
        self.assertEqual(status, 200)
        allocation = result['allocation']
        self.assertEqual(allocation['spent_minor'], 7470000)
        self.assertEqual(allocation['remaining_minor'], 30000)
        self.assertEqual(allocation['score_units'], '19380224213')
        self.assertEqual(sum(s['cost_minor'] for s in allocation['selections']), allocation['spent_minor'])
        self.assertEqual(sum(int(s['score_units']) for s in allocation['selections']), int(allocation['score_units']))
        self.assertEqual(len({s['building_id'] for s in allocation['selections']}), 30)
        payload = json.dumps(result, allow_nan=False, separators=(',', ':'))
        self.assertLess(len(payload.encode()), 1_000_000)
        self.assertEqual(result['schema_version'], 'heatshield.phase3a.v1')
        self.assertTrue(result['limitations'])
        self.assertTrue(result['assumptions'])
        for b in result['buildings']:
            for option in b['options']:
                self.assertEqual(len(option['simulation']['indoor_c']), 168)
        self.assertNotIn('simulation', allocation['selections'][0])

    def test_bounds_and_strict_types(self):
        invalid = [request(budget_minor=x) for x in (-1, True, 1.5, 100000001)]
        invalid += [request(threshold_c=x) for x in (True, None, '30', float('inf'), float('nan'), 14.9, 45.1)]
        invalid += [request(preset_id='other'), request(extra=1), {}, [], None]
        for data in invalid:
            with self.subTest(data=data):
                status, result = allocate_request(data)
                self.assertEqual(status, 422)
                self.assertNotIn('allocation', result)
        for budget, threshold in ((0, 15), (100000000, 45)):
            status, result = allocate_request(request(budget_minor=budget, threshold_c=threshold))
            self.assertEqual(status, 200)
            self.assertLessEqual(result['allocation']['spent_minor'], budget)

    def test_json_rejections(self):
        for body in (b'{', b'\xff', b'{"a":1,"a":2}', b'{"threshold_c":NaN}', b'[' * 1500):
            self.assertEqual(handle_json(body)[0], 400)
        self.assertEqual(handle_json(b' ' * 4097)[0], 413)
        self.assertEqual(handle_json(json.dumps(request()).encode())[0], 200)

    def test_state_failure_never_returns_partial_allocation(self):
        with patch('heatshield.api.allocations.allocate_portfolio', side_effect=StateLimitExceeded('private detail')):
            status, result = allocate_request(request())
        self.assertEqual(status, 422)
        self.assertEqual(result['error']['code'], 'OPTIMIZATION_STATE_LIMIT')
        self.assertNotIn('allocation', result)
        self.assertNotIn('private detail', json.dumps(result))

    def test_preset_resource_limits_and_internal_failure(self):
        scenarios = make_scenarios()
        from dataclasses import replace
        oversized = [scenarios * 2,
                     (replace(scenarios[0], weather=replace(scenarios[0].weather, hours=scenarios[0].weather.hours * 2)),),
                     (replace(scenarios[0], options=scenarios[0].options + (replace(scenarios[0].options[0], option_id='extra'),)),)]
        for preset in oversized:
            with patch('heatshield.api.allocations.make_scenarios', return_value=preset):
                self.assertEqual(allocate_request(request())[0], 500)
        with patch('heatshield.api.allocations.make_scenarios', side_effect=RuntimeError('sensitive')):
            status, result = allocate_request(request())
            self.assertEqual(status, 500)
            self.assertNotIn('sensitive', json.dumps(result))

    def test_http_transport(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = HTTPConnection(*server.server_address, timeout=10)
        try:
            connection.request('POST', '/api/allocations', json.dumps(request()), {'Content-Type': 'application/json'})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read())['allocation']['spent_minor'], 7470000)
            for method, path, headers, body, expected in (
                ('GET', '/api/allocations', {}, None, 405),
                ('POST', '/other', {}, '', 404),
                ('POST', '/api/allocations', {'Content-Type': 'text/plain'}, '{}', 415),
                ('POST', '/api/allocations', {'Content-Type': 'application/json'}, ' ' * 4097, 413),
                ('POST', '/api/allocations', {'Content-Type': 'application/json'}, '{', 400),
            ):
                connection.request(method, path, body, headers)
                response = connection.getresponse()
                self.assertEqual(response.status, expected)
                self.assertIn('error', json.loads(response.read()))
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join()
