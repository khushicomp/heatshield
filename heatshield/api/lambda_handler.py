"""API Gateway HTTP API payload-v2 adapter; no AWS SDK or scientific changes."""
import base64
import binascii
import json

from .allocations import MAX_BODY_BYTES, error, handle_json


def _response(result):
    status, payload = result
    return {'statusCode': status, 'headers': {
        'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store'
    }, 'isBase64Encoded': False,
        'body': json.dumps(payload, allow_nan=False, separators=(',', ':'))}


def handler(event, context):
    """CORS/preflight belong to API Gateway, not this adapter."""
    if not isinstance(event, dict) or event.get('version') != '2.0':
        return _response(error(400, 'INVALID_EVENT', 'Expected HTTP API payload version 2.0.'))
    request_context = event.get('requestContext')
    http = request_context.get('http') if isinstance(request_context, dict) else None
    if not isinstance(http, dict) or not isinstance(http.get('method'), str):
        return _response(error(400, 'INVALID_EVENT', 'Missing HTTP request context.'))
    if event.get('rawPath') != '/api/allocations':
        return _response(error(404, 'NOT_FOUND', 'Unknown endpoint.'))
    if http['method'] != 'POST':
        return _response(error(405, 'METHOD_NOT_ALLOWED', 'Use POST /api/allocations.'))
    headers = event.get('headers', {})
    if not isinstance(headers, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                            for k, v in headers.items()):
        return _response(error(400, 'INVALID_EVENT', 'Invalid request headers.'))
    content_type = [v for k, v in headers.items() if k.lower() == 'content-type']
    if len(content_type) != 1 or content_type[0].split(';')[0].strip().lower() != 'application/json':
        return _response(error(415, 'UNSUPPORTED_MEDIA_TYPE', 'Use application/json.'))
    body = event.get('body', '')
    encoded = event.get('isBase64Encoded', False)
    if not isinstance(body, str) or type(encoded) is not bool:
        return _response(error(400, 'INVALID_BODY', 'Expected a string body and boolean encoding flag.'))
    max_encoded = ((MAX_BODY_BYTES + 2) // 3) * 4
    if len(body) > (max_encoded if encoded else MAX_BODY_BYTES):
        return _response(error(413, 'REQUEST_TOO_LARGE', 'Maximum request size is 4096 bytes.'))
    try:
        decoded = base64.b64decode(body, validate=True) if encoded else body.encode('utf-8')
    except (ValueError, UnicodeError, binascii.Error):
        return _response(error(400, 'INVALID_BODY', 'Invalid body encoding.'))
    try:
        return _response(handle_json(decoded))
    except Exception:
        return _response(error(500, 'INTERNAL_ERROR', 'Allocation could not be completed; no allocation was returned.'))
