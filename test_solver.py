# Adaptive API Gateway Server
An implementation of the **Adaptive API Gateway Challenge**. This server exposes a `POST /solve` endpoint that bridges legacy V1 and V2 models (`adaptInput` -> `adaptOutput`) while processing service heartbeat telemetry data to calculate SLO metrics (`sloOutput`).
An implementation of the **Adaptive API Gateway Challenge** in **Python** (and Node.js). This server exposes a `POST /solve` endpoint that bridges legacy V1 and V2 models (`adaptInput` -> `adaptOutput`) while processing service heartbeat telemetry data to calculate SLO metrics (`sloOutput`).
---
## Files Overview
|
 File 
|
 Language 
|
 Purpose 
|
|
:---
|
:---
|
:---
|
|
[
`solver.py`
](
file:///C:/Users/jia53/.gemini/antigravity/scratch/adaptive-gateway/solver.py
)
|
 Python 
|
 Core logic (payload decoding, adaptation, SLO calculations) 
|
|
[
`server.py`
](
file:///C:/Users/jia53/.gemini/antigravity/scratch/adaptive-gateway/server.py
)
|
 Python 
|
 HTTP server exposing 
`POST /solve`
|
|
[
`test_solver.py`
](
file:///C:/Users/jia53/.gemini/antigravity/scratch/adaptive-gateway/test_solver.py
)
|
 Python 
|
 Unit and integration test suite 
|
|
[
`solver.js`
](
file:///C:/Users/jia53/.gemini/antigravity/scratch/adaptive-gateway/solver.js
)
|
 Node.js 
|
 Node implementation of core logic 
|
|
[
`server.js`
](
file:///C:/Users/jia53/.gemini/antigravity/scratch/adaptive-gateway/server.js
)
|
 Node.js 
|
 Node HTTP server 
|
|
[
`test.js`
](
file:///C:/Users/jia53/.gemini/antigravity/scratch/adaptive-gateway/test.js
)
|
 Node.js 
|
 Node test suite 
|
---
## Technical Features
### 1. Payload Decoding (`decodePayload`)
### 1. Payload Decoding (`decode_payload`)
Handles multiple payload delivery forms transparently:
- Base64-encoded JSON strings (standard format requested by client)
- Direct JSON strings
- **Filtering**: Keeps heartbeats matching `sloQuery.service` with `timestamp >= sloQuery.since`.
- **Availability**: Ratio of `"OK"` status heartbeats over total filtered heartbeats:
  $$\text{availability} = \frac{\text{Count of "OK" heartbeats}}{\text{Total filtered heartbeats}}$$
- **P95 Latency (`p95LatencyMs`)**: Sorted ascending latency array using the Nearest-Rank method:
- **P95 Latency (`p95LatencyMs`)**: Sorted ascending latency array using Nearest-Rank method:
  $$\text{Index} = \max(0, \lceil 0.95 \times N \rceil - 1)$$
---
---
## How to Run & Test
## How to Run & Test (Python)
### Run Tests
```bash
node test.js
# or
npm test
python test_solver.py
```
### Start Server
```bash
node server.js
# or
npm start
python server.py
```
The server will start listening on port `3000` (or `process.env.PORT`).
The server will start listening on port `3000` (or `PORT` environment variable).
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
"""
Adaptive API Gateway Challenge - Core Logic (Python)
"""
import base64
import json
import math
from typing import Any, Dict
def decode_payload(req_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decodes payload from request body.
    Handles Base64 encoded strings, raw JSON strings, or direct dict objects.
    """
    if not isinstance(req_body, dict):
        return {}
    raw_payload = req_body.get('payload', req_body)
    if isinstance(raw_payload, str):
        # 1. Try decoding Base64 first
        try:
            decoded_bytes = base64.b64decode(raw_payload)
            decoded_str = decoded_bytes.decode('utf-8')
            parsed = json.loads(decoded_str)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        # 2. Try direct JSON parsing
        try:
            parsed = json.loads(raw_payload)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    elif isinstance(raw_payload, dict):
        return raw_payload
    return {}
def parse_priority(pri: Any) -> int:
    """
    Maps priority strings/numbers to standard integer priority.
    LOW -> 1
    MEDIUM/MED -> 2
    HIGH -> 3
    CRITICAL/URGENT -> 4
    """
    if pri is None:
        return 0
    if isinstance(pri, (int, float)):
        return int(pri)
    pri_str = str(pri).strip().upper()
    if pri_str in ('LOW', '1'):
        return 1
    if pri_str in ('MEDIUM', 'MED', 'NORMAL', '2'):
        return 2
    if pri_str in ('HIGH', '3'):
        return 3
    if pri_str in ('CRITICAL', 'URGENT', '4'):
        return 4
    try:
        return int(pri_str)
    except ValueError:
        return 0
def solve_challenge(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes adaptInput, heartbeats, and sloQuery to construct response.
    Returns:
    {
        "adaptOutput": {
            "id": str,
            "name": str,
            "action": str,
            "priority": int
        },
        "sloOutput": {
            "availability": float,
            "p95LatencyMs": int/float
        }
    }
    """
    adapt_input = data.get('adaptInput') or {}
    heartbeats = data.get('heartbeats') or []
    if not isinstance(heartbeats, list):
        heartbeats = []
    slo_query = data.get('sloQuery') or {}
    # --- 1. Transform adaptInput -> adaptOutput ---
    user = adapt_input.get('user') or {}
    metadata = adapt_input.get('metadata') or {}
    user_id = (
        user.get('id')
        or user.get('userId')
        or adapt_input.get('id')
        or adapt_input.get('userId')
        or ''
    )
    name = (
        user.get('fullName')
        or user.get('name')
        or adapt_input.get('fullName')
        or adapt_input.get('name')
        or ''
    )
    action = str(adapt_input.get('action') or '').lower()
    raw_priority = metadata.get('priority') if 'priority' in metadata else adapt_input.get('priority')
    priority = parse_priority(raw_priority)
    adapt_output = {
        'id': user_id,
        'name': name,
        'action': action,
        'priority': priority
    }
    # --- 2. Compute SLO metrics -> sloOutput ---
    target_service = slo_query.get('service')
    since_timestamp = slo_query.get('since')
    filtered_hb = []
    for hb in heartbeats:
        if not isinstance(hb, dict):
            continue
        # Service match filter
        if target_service is not None and target_service != '':
            if hb.get('service') != target_service:
                continue
        # Timestamp match filter (since is inclusive: timestamp >= since)
        if since_timestamp is not None:
            hb_ts = hb.get('timestamp')
            if isinstance(hb_ts, (int, float)) and hb_ts < since_timestamp:
                continue
        filtered_hb.append(hb)
    availability = 0.0
    p95_latency_ms = 0
    if filtered_hb:
        # Count "OK" status
        ok_count = sum(
            1 for hb in filtered_hb if str(hb.get('status', '')).upper() == 'OK'
        )
        availability = ok_count / len(filtered_hb)
        # Extract latencies
        latencies = []
        for hb in filtered_hb:
            lat = hb.get('latencyMs')
            if lat is not None:
                try:
                    latencies.append(float(lat))
                except (ValueError, TypeError):
                    pass
        latencies.sort()
        if latencies:
            # Nearest-rank 95th percentile index: max(0, ceil(0.95 * N) - 1)
            p95_idx = max(0, math.ceil(0.95 * len(latencies)) - 1)
            p95_val = latencies[p95_idx]
            p95_latency_ms = int(p95_val) if p95_val.is_integer() else p95_val
    return {
        'adaptOutput': adapt_output,
        'sloOutput': {
            'availability': availability,
            'p95LatencyMs': p95_latency_ms
        }
    }
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
