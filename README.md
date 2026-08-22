markdown
# Adaptive API Gateway Challenge – Python Solution

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
Run the server:

bash
python app.py
The server will start on http://localhost:3000.

Endpoint
POST /solve

Request body: { "payload": "<base64-encoded JSON>" }

Response: { "adaptOutput": {...}, "sloOutput": {...} }

Testing with curl
bash
curl -X POST http://localhost:3000/solve \
  -H "Content-Type: application/json" \
  -d '{"payload":"ewoJImFkYXB0SW5wdXQiOiB7CgkJInVzZXIiOiB7CgkJCSJpZCI6ICJVNDIiLAoJCQkiZnVsbE5hbWUiOiAiSmFuZSBEb2UiCgkJfSwKCQkiYWN0aW9uIjogIkNSRUFURSIsCgkJIm1ldGFkYXRhIjogewoJCQkicHJpb3JpdHkiOiAiSElHSCIKCQl9Cgl9LAoJImhlYXJ0YmVhdHMiOiBbCgkJewoJCQkic2VydmljZSI6ICJhdXRoIiwKCQkJInRpbWVzdGFtcCI6IDE3MTAwMDAxMjMsCgkJCSJsYXRlbmN5TXMiOiAxMjAsCgkJCSJzdGF0dXMiOiAiT0siCgkJfSwKCQl7CgkJCSJzZXJ2aWNlIjogImF1dGgiLAoJCQkidGltZXN0YW1wIjogMTcxMDAwMDEyNSwKCQkJImxhdGVuY3lNcyI6IDE4MCwKCQkJInN0YXR1cyI6ICJGQUlMIgoJCX0sCgkJewoJCQkic2VydmljZSI6ICJhdXRoIiwKCQkJInRpbWVzdGFtcCI6IDE3MTAwMDAxMjEsCgkJCSJsYXRlbmN5TXMiOiA5NSwKCQkJInN0YXR1cyI6ICJPSyIKCQl9CgldLAoJInNsb1F1ZXJ5IjogewoJCSJzZXJ2aWNlIjogImF1dGgiLAoJCSJzaW5jZSI6IDE3MTAwMDAxMjMKCX0KfQ=="}'
Expected output:

json
{
  "adaptOutput": {
    "id": "U42",
    "name": "Jane Doe",
    "action": "create",
    "priority": 3
  },
  "sloOutput": {
    "availability": 0.5,
    "p95LatencyMs": 180
  }
}
Optional test script
You can also use the included test_client.py to send the sample request and print the response.

text

---

### File 4 (optional): `test_client.py`

```python
import requests
import json

url = 'http://localhost:3000/solve'
payload = {
    "payload": "ewoJImFkYXB0SW5wdXQiOiB7CgkJInVzZXIiOiB7CgkJCSJpZCI6ICJVNDIiLAoJCQkiZnVsbE5hbWUiOiAiSmFuZSBEb2UiCgkJfSwKCQkiYWN0aW9uIjogIkNSRUFURSIsCgkJIm1ldGFkYXRhIjogewoJCQkicHJpb3JpdHkiOiAiSElHSCIKCQl9Cgl9LAoJImhlYXJ0YmVhdHMiOiBbCgkJewoJCQkic2VydmljZSI6ICJhdXRoIiwKCQkJInRpbWVzdGFtcCI6IDE3MTAwMDAxMjMsCgkJCSJsYXRlbmN5TXMiOiAxMjAsCgkJCSJzdGF0dXMiOiAiT0siCgkJfSwKCQl7CgkJCSJzZXJ2aWNlIjogImF1dGgiLAoJCQkidGltZXN0YW1wIjogMTcxMDAwMDEyNSwKCQkJImxhdGVuY3lNcyI6IDE4MCwKCQkJInN0YXR1cyI6ICJGQUlMIgoJCX0sCgkJewoJCQkic2VydmljZSI6ICJhdXRoIiwKCQkJInRpbWVzdGFtcCI6IDE3MTAwMDAxMjEsCgkJCSJsYXRlbmN5TXMiOiA5NSwKCQkJInN0YXR1cyI6ICJPSyIKCQl9CgldLAoJInNsb1F1ZXJ5IjogewoJCSJzZXJ2aWNlIjogImF1dGgiLAoJCSJzaW5jZSI6IDE3MTAwMDAxMjMKCX0KfQ=="
}

response = requests.post(url, json=payload)
print(response.status_code)
print(json.dumps(response.json(), indent=2))
