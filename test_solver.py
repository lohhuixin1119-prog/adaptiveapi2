"""
Test suite for Adaptive API Gateway Challenge (Python)
"""
import json
import threading
import time
import unittest
import urllib.request
from http.server import HTTPServer
from solver import decode_payload, parse_priority, solve_challenge
from server import GatewayHandler
TEST_PORT = 3002
class TestAdaptiveGateway(unittest.TestCase):
    def setUp(self):
        self.sample_payload_b64 = "ewoJImFkYXB0SW5wdXQiOiB7CgkJInVzZXIiOiB7CgkJCSJpZCI6ICJVNDIiLAoJCQkiZnVsbE5hbWUiOiAiSmFuZSBEb2UiCgkJfSwKCQkiYWN0aW9uIjogIkNSRUFURSIsCgkJIm1ldGFkYXRhIjogewoJCQkicHJpb3JpdHkiOiAiSElHSCIKCQl9Cgl9LAoJImhlYXJ0YmVhdHMiOiBbCgkJewoJCQkic2VydmljZSI6ICJhdXRoIiwKCQkJInRpbWVzdGFtcCI6IDE3MTAwMDAxMjMsCgkJCSJsYXRlbmN5TXMsIDEyMCwKCQkJInN0YXR1cyI6ICJPSyIKCQl9LAoJCXsKCQkJInNlcnZpY2UiOiAiYXV0aCIsCgkJCSJ0aW1lc3RhbXAiOiAxNzEwMDAwMTI1LAoJCQksYXRlbmN5TXMsIDE4MCwKCQkJInN0YXR1cyI6ICJGQUlMIgoJCX0sCgkJewoJCQkic2VydmljZSI6ICJhdXRoIiwKCQkJInRpbWVzdGFtcCI6IDE3MTAwMDAxMjEsCgkJCSJsYXRlbmN5TXMsIDk1LAoJCQkic3RhdHVzIjogIk9LIgoJCX0KCV0sCgkic2xvUXVlcnkiOiB7CgkJInNlcnZpY2UiOiAiYXV0aCIsCgkJInNpbmNlIjogMTcxMDAwMDEyMwoJfQp9"
    def test_decode_payload(self):
        req = {"payload": self.sample_payload_b64}
        decoded = decode_payload(req)
        self.assertIn("adaptInput", decoded)
        self.assertEqual(decoded["adaptInput"]["user"]["id"], "U42")
        self.assertEqual(decoded["adaptInput"]["user"]["fullName"], "Jane Doe")
        self.assertEqual(decoded["adaptInput"]["action"], "CREATE")
        self.assertEqual(decoded["adaptInput"]["metadata"]["priority"], "HIGH")
    def test_solve_challenge_sample(self):
        req = {"payload": self.sample_payload_b64}
        decoded = decode_payload(req)
        res = solve_challenge(decoded)
        expected_adapt = {
            "id": "U42",
            "name": "Jane Doe",
            "action": "create",
            "priority": 3
        }
        expected_slo = {
            "availability": 0.5,
            "p95LatencyMs": 180
        }
        self.assertEqual(res["adaptOutput"], expected_adapt)
        self.assertEqual(res["sloOutput"], expected_slo)
    def test_priority_parsing(self):
        self.assertEqual(parse_priority("LOW"), 1)
        self.assertEqual(parse_priority("MEDIUM"), 2)
        self.assertEqual(parse_priority("HIGH"), 3)
        self.assertEqual(parse_priority("CRITICAL"), 4)
        self.assertEqual(parse_priority("URGENT"), 4)
        self.assertEqual(parse_priority(2), 2)
    def test_multi_service_and_timestamp_filter(self):
        data = {
            "adaptInput": {"user": {"id": "U1", "fullName": "Alice"}, "action": "UPDATE", "metadata": {"priority": "LOW"}},
            "heartbeats": [
                {"service": "auth", "timestamp": 100, "latencyMs": 50, "status": "OK"},
                {"service": "db", "timestamp": 200, "latencyMs": 500, "status": "FAIL"},
                {"service": "auth", "timestamp": 200, "latencyMs": 100, "status": "OK"},
                {"service": "auth", "timestamp": 300, "latencyMs": 150, "status": "OK"},
                {"service": "auth", "timestamp": 400, "latencyMs": 200, "status": "FAIL"}
            ],
            "sloQuery": {"service": "auth", "since": 200}
        }
        res = solve_challenge(data)
        self.assertEqual(res["sloOutput"]["p95LatencyMs"], 200)
        self.assertAlmostEqual(res["sloOutput"]["availability"], 2/3, places=2)
    def test_http_endpoint_post_solve(self):
        server_address = ('127.0.0.1', TEST_PORT)
        httpd = HTTPServer(server_address, GatewayHandler)
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
