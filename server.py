"""
Adaptive API Gateway Challenge - HTTP Server (Python)
Exposes POST /solve
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from solver import decode_payload, solve_challenge
class GatewayHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    def do_OPTIONS(self):
        self._set_headers(204)
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
    def do_POST(self):
        if self.path in ('/solve', '/solve/'):
            content_length = int(self.headers.get('Content-Length', 0))
            body_bytes = self.rfile.read(content_length)
            try:
                body_str = body_bytes.decode('utf-8') if body_bytes else '{}'
                parsed_body = json.loads(body_str) if body_str.strip() else {}
                # Decode payload (handles Base64 strings, direct JSON strings, or objects)
                payload_data = decode_payload(parsed_body)
                # Solve challenge
                result = solve_challenge(payload_data)
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
def run_server(port=3000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, GatewayHandler)
    print(f'Adaptive API Gateway running on port {port}...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer shutting down.')
        httpd.server_close()
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    run_server(port)
