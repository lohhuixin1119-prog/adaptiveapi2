"""
Adaptive API Gateway Challenge - HTTP Server (Python)
Adaptive API Gateway Challenge - Production WSGI Server (Python)
Compatible with Gunicorn, Waitress, uWSGI, and standalone execution.
Exposes POST /solve
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from solver import decode_payload, solve_challenge
class GatewayHandler(BaseHTTPRequestHandler):
def app(environ, start_response):
    """WSGI Application interface for Gunicorn / Render / uWSGI."""
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', '')
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    headers = [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type')
    ]
    def do_OPTIONS(self):
        self._set_headers(204)
    # Handle CORS OPTIONS request
    if method == 'OPTIONS':
        start_response('204 No Content', headers)
        return [b'']
    def do_GET(self):
        if self.path in ('/', '/health', '/health/'):
            self._set_headers(200)
            res = {
                'status': 'ok',
                'message': 'Adaptive API Gateway (Python) server running'
            }
            self.wfile.write(json.dumps(res).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not Found'}).encode('utf-8'))
    # Health check endpoint
    if path in ('/', '/health', '/health/') and method == 'GET':
        start_response('200 OK', headers)
        res = {
            'status': 'ok',
            'message': 'Adaptive API Gateway (Python) running'
        }
        return [json.dumps(res).encode('utf-8')]
    def do_POST(self):
        if self.path in ('/solve', '/solve/'):
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
    # POST /solve endpoint
    if path in ('/solve', '/solve/') and method == 'POST':
        try:
            try:
                body_str = body_bytes.decode('utf-8') if body_bytes else '{}'
                parsed_body = json.loads(body_str) if body_str.strip() else {}
                content_length = int(environ.get('CONTENT_LENGTH', 0))
            except (ValueError, TypeError):
                content_length = 0
                # Decode payload (handles Base64 strings, direct JSON strings, or objects)
                payload_data = decode_payload(parsed_body)
            body_bytes = (
                environ['wsgi.input'].read(content_length)
                if content_length > 0
                else b''
            )
                # Solve challenge
                result = solve_challenge(payload_data)
            body_str = body_bytes.decode('utf-8') if body_bytes else '{}'
            parsed_body = json.loads(body_str) if body_str.strip() else {}
                self._set_headers(200)
                self.wfile.write(json.dumps(result, indent=2).encode('utf-8'))
            except Exception as e:
                self._set_headers(400)
                err_res = {
                    'error': 'Bad Request',
                    'message': str(e)
                }
                self.wfile.write(json.dumps(err_res).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not Found'}).encode('utf-8'))
            # Decode base64 or raw payload
            payload_data = decode_payload(parsed_body)
            # Process solver logic
            result = solve_challenge(payload_data)
def run_server(port=3000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, GatewayHandler)
    print(f'Adaptive API Gateway running on port {port}...')
            start_response('200 OK', headers)
            return [json.dumps(result, indent=2).encode('utf-8')]
        except Exception as e:
            start_response('400 Bad Request', headers)
            err_res = {
                'error': 'Bad Request',
                'message': str(e)
            }
            return [json.dumps(err_res).encode('utf-8')]
    # 404 for non-existent paths
    start_response('404 Not Found', headers)
    return [json.dumps({'error': 'Not Found'}).encode('utf-8')]
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    port = int(os.environ.get('PORT', 3000))
    print(f'Starting Adaptive API Gateway WSGI server on port {port}...')
    httpd = make_server('', port, app)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer shutting down.')
        httpd.server_close()
        print('\nServer stopped.')
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    run_server(port)
