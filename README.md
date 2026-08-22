Overview

Review Changes




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
