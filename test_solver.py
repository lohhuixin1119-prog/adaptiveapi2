"""
Test suite for Adaptive API Gateway Challenge (Python)
Test suite for Adaptive API Gateway Challenge (Python WSGI & FastAPI)
"""
import json
import threading
import time
import unittest
import urllib.request
from http.server import HTTPServer
from wsgiref.simple_server import make_server
from solver import decode_payload, parse_priority, solve_challenge
from server import GatewayHandler
from server import app as wsgi_app
TEST_PORT = 3002
TEST_PORT = 3003
class TestAdaptiveGateway(unittest.TestCase):
        self.assertAlmostEqual(res["sloOutput"]["availability"], 2/3, places=2)
    def test_http_endpoint_post_solve(self):
        server_address = ('127.0.0.1', TEST_PORT)
        httpd = HTTPServer(server_address, GatewayHandler)
        httpd = make_server('127.0.0.1', TEST_PORT, wsgi_app)
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)
        url = f"http://127.0.0.1:{TEST_PORT}/solve"
        body = json.dumps({"payload": self.sample_payload_b64}).encode('utf-8')
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as response:
            self.assertEqual(response.status, 200)
            res_data = json.loads(response.read().decode('utf-8'))
            self.assertEqual(res_data["adaptOutput"]["id"], "U42")
            self.assertEqual(res_data["adaptOutput"]["name"], "Jane Doe")
            self.assertEqual(res_data["adaptOutput"]["action"], "create")
            self.assertEqual(res_data["adaptOutput"]["priority"], 3)
            self.assertEqual(res_data["sloOutput"]["availability"], 0.5)
            self.assertEqual(res_data["sloOutput"]["p95LatencyMs"], 180)
        httpd.shutdown()
        httpd.server_close()
if __name__ == "__main__":
    unittest.main()
