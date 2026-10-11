import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from heatshield.api.lambda_handler import handler
from heatshield.api.allocations import allocate_request
from scripts.package_lambda import MODULES, package

REQUEST = {'preset_id': 'synthetic_municipal_v1', 'budget_minor': 7500000, 'threshold_c': 30}


def event(**changes):
    return {'version': '2.0', 'rawPath': '/api/allocations', 'requestContext': {'http': {'method': 'POST'}},
            'headers': {'content-type': 'application/json'}, 'body': json.dumps(REQUEST),
            'isBase64Encoded': False, **changes}


class LambdaTests(unittest.TestCase):
    def test_plain_and_base64_preserve_service_results(self):
        expected = allocate_request(REQUEST)[1]
        for incoming in (event(), event(body=base64.b64encode(json.dumps(REQUEST).encode()).decode(), isBase64Encoded=True)):
            response = handler(incoming, None)
            self.assertEqual(response['statusCode'], 200)
            self.assertEqual(json.loads(response['body']), expected)
            self.assertFalse(response['isBase64Encoded'])
            self.assertEqual(response['headers']['cache-control'], 'no-store')
            self.assertNotIn('access-control-allow-origin', response['headers'])
            self.assertLess(len(response['body'].encode()), 1_000_000)

    def test_event_method_path_and_media_validation(self):
        for incoming, expected in (
            (None, 400), ({}, 400), (event(version='1.0'), 400),
            (event(requestContext=None), 400), (event(rawPath='/other'), 404),
            (event(requestContext={'http': {'method': 'GET'}}), 405),
            (event(headers={}), 415), (event(headers={'Content-Type': 'text/plain'}), 415),
            (event(headers={'content-type': None}), 400), (event(body=None), 400),
            (event(isBase64Encoded='true'), 400),
        ):
            with self.subTest(incoming=incoming):
                response = handler(incoming, None)
                self.assertEqual(response['statusCode'], expected)
                self.assertIn('error', json.loads(response['body']))
        self.assertEqual(handler(event(headers={'Content-Type': 'application/json; charset=utf-8'}), None)['statusCode'], 200)

    def test_body_limits_apply_to_decoded_utf8_bytes(self):
        cases = [event(body=' ' * 4097), event(body='é' * 2049),
                 event(body=base64.b64encode(b' ' * 4097).decode(), isBase64Encoded=True),
                 event(body='A' * 6000, isBase64Encoded=True)]
        for incoming in cases:
            self.assertEqual(handler(incoming, None)['statusCode'], 413)
        valid = json.dumps(REQUEST).encode()
        for body in (valid.ljust(4096, b' '),):
            self.assertEqual(handler(event(body=body.decode()), None)['statusCode'], 200)
            self.assertEqual(handler(event(body=base64.b64encode(body).decode(), isBase64Encoded=True), None)['statusCode'], 200)

    def test_invalid_encoding_and_json(self):
        for incoming in (event(body='@@', isBase64Encoded=True), event(body='\ud800'),
                         event(body=base64.b64encode(b'\xff').decode(), isBase64Encoded=True),
                         event(body='{'), event(body='{"a":1,"a":2}'), event(body='NaN')):
            self.assertEqual(handler(incoming, None)['statusCode'], 400)
        self.assertEqual(handler(event(body=json.dumps({**REQUEST, 'budget_minor': -1})), None)['statusCode'], 422)

    def test_service_failures_are_not_partial_success(self):
        from heatshield.optimization import StateLimitExceeded
        with patch('heatshield.api.allocations.allocate_portfolio', side_effect=StateLimitExceeded()):
            response = handler(event(), None)
            self.assertEqual(response['statusCode'], 422)
            self.assertEqual(json.loads(response['body'])['error']['code'], 'OPTIMIZATION_STATE_LIMIT')
        with patch('heatshield.api.lambda_handler.handle_json', side_effect=RuntimeError('private')):
            response = handler(event(), None)
            self.assertEqual(response['statusCode'], 500)
            self.assertNotIn('private', response['body'])

    def test_allowlisted_deterministic_zip_runs_in_isolation(self):
        output = Path(__file__).resolve().parents[1] / 'outputs'
        output.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output) as directory:
            first = package(Path(directory) / 'first.zip')
            second = package(Path(directory) / 'second.zip')
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with ZipFile(first) as archive:
                self.assertEqual(set(archive.namelist()), {'heatshield/' + name for name in MODULES})
            code = ('import sys,json;sys.path.insert(0,sys.argv[1]);'
                    'from heatshield.api.lambda_handler import handler;'
                    'r=handler(json.loads(sys.argv[2]),None);'
                    'assert r["statusCode"]==200;'
                    'assert json.loads(r["body"])["allocation"]["score_units"]=="19380224213"')
            subprocess.run([sys.executable, '-B', '-I', '-c', code, str(first), json.dumps(event())], check=True, timeout=15)
