# Adaptive API Gateway

Implements `POST /solve` per the challenge spec.

## Run

```bash
pip install -r requirements.txt
python3 main.py
# or: uvicorn main:app --host 0.0.0.0 --port 8080
```

## Test

```bash
curl -s -X POST http://localhost:8080/solve \
  -H 'Content-Type: application/json' \
  -d '{"payload": "ewoJImFkYXB0SW5wdXQiOiB7CgkJInVzZXIiOiB7CgkJCSJpZCI6ICJVNDIiLAoJCQkiZnVsbE5hbWUiOiAiSmFuZSBEb2UiCgkJfSwKCQkiYWN0aW9uIjogIkNSRUFURSIsCgkJIm1ldGFkYXRhIjogewoJCQkicHJpb3JpdHkiOiAiSElHSCIKCQl9Cgl9LAoJImhlYXJ0YmVhdHMiOiBbCgkJewoJCQkic2VydmljZSI6ICJhdXRoIiwKCQkJInRpbWVzdGFtcCI6IDE3MTAwMDAxMjMsCgkJCSJsYXRlbmN5TXMiOiAxMjAsCgkJCSJzdGF0dXMiOiAiT0siCgkJfSwKCQl7CgkJCSJzZXJ2aWNlIjogImF1dGgiLAoJCQkidGltZXN0YW1wIjogMTcxMDAwMDEyNSwKCQkJImxhdGVuY3lNcyI6IDE4MCwKCQkJInN0YXR1cyI6ICJGQUlMIgoJCX0sCgkJewoJCQkic2VydmljZSI6ICJhdXRoIiwKCQkJInRpbWVzdGFtcCI6IDE3MTAwMDAxMjEsCgkJCSJsYXRlbmN5TXMiOiA5NSwKCQkJInN0YXR1cyI6ICJPSyIKCQl9CgldLAoJInNsb1F1ZXJ5IjogewoJCSJzZXJ2aWNlIjogImF1dGgiLAoJCSJzaW5jZSI6IDE3MTAwMDAxMjMKCX0KfQ=="}'
```

Expected output (matches the spec exactly):

```json
{
  "adaptOutput": {"id": "U42", "name": "Jane Doe", "action": "create", "priority": 3},
  "sloOutput": {"availability": 0.5, "p95LatencyMs": 180}
}
```

`test_edge_cases.py` covers 7 scenarios (exact sample, no matching heartbeats,
missing priority, unknown priority, all-OK heartbeats, a single heartbeat,
and the `since` boundary) — run with `python3 test_edge_cases.py` while the
server is up.

## Logic

**`adaptOutput`** (V1 -> V2 field adapter)
| field | source |
|---|---|
| `id` | `adaptInput.user.id` |
| `name` | `adaptInput.user.fullName` |
| `action` | `adaptInput.action`, lower-cased |
| `priority` | `adaptInput.metadata.priority` mapped `LOW=1, MEDIUM=2, HIGH=3, CRITICAL=4`; missing/unrecognized → `0` |

**`sloOutput`** (heartbeat health)
1. Filter `heartbeats` to `service == sloQuery.service AND timestamp >= sloQuery.since` (boundary inclusive).
2. `availability` = OK count / filtered count.
3. `p95LatencyMs` = 95th percentile of filtered `latencyMs`, nearest-rank method: sort ascending, take the `ceil(0.95 * n)`-th value (1-indexed). This is what reproduces `180` in the worked example (`n=2` → index `ceil(1.9)=2` → 2nd value).
4. If nothing matches the filter: `availability = 0.0`, `p95LatencyMs = 0`.

Payload decoding accepts standard or URL-safe base64, with or without
padding, and unknown/extra JSON fields anywhere in the request are ignored
rather than rejected.
