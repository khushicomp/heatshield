"""Loopback-only local demonstration transport, not a production web server."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .allocations import MAX_BODY_BYTES, error, handle_json


class Handler(BaseHTTPRequestHandler):
    def reply(self, response):
        status, payload = response
        body = json.dumps(payload, allow_nan=False, separators=(',', ':')).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.connection.settimeout(10)
        if self.path != '/api/allocations':
            return self.reply(error(404, 'NOT_FOUND', 'Unknown endpoint.'))
        if self.headers.get('Transfer-Encoding'):
            return self.reply(error(400, 'INVALID_REQUEST', 'Transfer encoding is unsupported.'))
        if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            return self.reply(error(415, 'UNSUPPORTED_MEDIA_TYPE', 'Use application/json.'))
        try:
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or not lengths[0].isdigit():
                raise ValueError()
            size = int(lengths[0])
            if size > MAX_BODY_BYTES:
                return self.reply(error(413, 'REQUEST_TOO_LARGE', 'Maximum request size is 4096 bytes.'))
            body = self.rfile.read(size)
            if len(body) != size:
                raise ValueError()
        except (ValueError, TimeoutError):
            return self.reply(error(400, 'INVALID_REQUEST', 'Expected a complete body and valid Content-Length.'))
        self.reply(handle_json(body))

    def do_GET(self):
        self.reply(error(405 if self.path == '/api/allocations' else 404,
                         'METHOD_NOT_ALLOWED' if self.path == '/api/allocations' else 'NOT_FOUND',
                         'Use POST /api/allocations.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1', args.port), Handler) as server:
        print(f'HeatShield local API: http://127.0.0.1:{args.port}', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
