import base64
import math
import orjson
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

# Default to ORJSONResponse for lightning-fast output serialization
app = FastAPI(default_response_class=ORJSONResponse)

PRIORITY_MAP = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

@app.post("/solve")
async def solve_extreme(request: Request):
    # 1. Bypass Pydantic: Parse the outer JSON natively
    body = await request.json()
    
    # 2. Ultra-fast Decode: orjson parses raw bytes directly
    raw_bytes = base64.b64decode(body["payload"])
    data = orjson.loads(raw_bytes)

    # 3. Adapt Input (O(1) Access)
    adapt_in = data["adaptInput"]
    metadata = adapt_in.get("metadata", {})
    
    adapt_out = {
        "id": adapt_in["user"]["id"],
        "name": adapt_in["user"]["fullName"],
        "action": adapt_in["action"].lower(),
        "priority": PRIORITY_MAP.get(metadata.get("priority", "LOW").upper(), 1)
    }

    # 4. Filter and Calculate
    slo_query = data.get("sloQuery", {})
    target_service = slo_query.get("service")
    target_since = slo_query.get("since", 0)
    
    latencies = []
    ok_count = 0
    
    for hb in data.get("heartbeats", []):
        if hb.get("service") == target_service and hb.get("timestamp", 0) >= target_since:
            latencies.append(hb.get("latencyMs", 0))
            if hb.get("status") == "OK":
                ok_count += 1
                
    total = len(latencies)
    if total == 0:
        return {"adaptOutput": adapt_out, "sloOutput": {"availability": 0.0, "p95LatencyMs": 0}}
        
    latencies.sort()
    p95_idx = max(0, math.ceil(0.95 * total) - 1)
    
    return {
        "adaptOutput": adapt_out,
        "sloOutput": {
            "availability": ok_count / total,
            "p95LatencyMs": latencies[p95_idx]
        }
    }
