# Adaptive API Gateway Challenge

## Requirements

Python 3.9+ recommended.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

The API will run at:

http://localhost:8000

## Endpoint

POST /solve

Request:

```json
{
  "payload": "<base64 encoded JSON>"
}
```

The payload is decoded from Base64 and then parsed as JSON.

The server:
1. Converts adaptInput into adaptOutput.
2. Filters heartbeats by service and since.
3. Calculates availability.
4. Calculates P95 latency using nearest-rank percentile.

## Example output

```json
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
```
