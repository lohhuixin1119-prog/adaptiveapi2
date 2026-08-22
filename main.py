from fastapi import FastAPI
from pydantic import BaseModel
import base64
import json
import math

app = FastAPI()

# Pre-allocate dictionary in memory for O(1) lookups
PRIORITY_MAP = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4
}

# Only validate the outermost layer to satisfy the framework requirement
class SolveRequest(BaseModel):
    payload: str

@app.post("/solve")
def solve_fast(request: SolveRequest):
    # 1. Fast Decode: Load JSON directly into native Python dictionaries
    data = json.loads(base64.b64decode(request.payload))

    # 2. Fast Adapt: O(1) dictionary access
    adapt_in = data["adaptInput"]
    metadata = adapt_in.get("metadata", {})
    
    adapt_out = {
        "id": adapt_in["user"]["id"],
        "name": adapt_in["user"]["fullName"],
        "action": adapt_in["action"].lower(),
        "priority": PRIORITY_MAP.get(metadata.get("priority", "LOW").upper(), 1)
    }

    # 3. Fast Metrics: Single-Pass O(N) Processing
    slo_query = data.get("sloQuery", {})
    target_service = slo_query.get("service")
    target_since = slo_query.get("since", 0)
    
    ok_count = 0
    latencies = []
    
    # We loop through the data exactly ONCE. 
    # Using `.get()` avoids KeyError checks while remaining highly optimized.
    for hb in data.get("heartbeats", []):
        if hb.get("service") == target_service and hb.get("timestamp", 0) >= target_since:
            latencies.append(hb.get("latencyMs", 0))
            if hb.get("status") == "OK":
                ok_count += 1
                
    total_filtered = len(latencies)
    
    # Handle zero-division edge case immediately
    if total_filtered == 0:
        return {
            "adaptOutput": adapt_out,
            "sloOutput": {"availability": 0.0, "p95LatencyMs": 0}
        }
        
    # 4. Fast Percentile: O(K log K) sort only on the filtered subset
    latencies.sort()
    p95_index = max(0, math.ceil(0.95 * total_filtered) - 1)
    
    return {
        "adaptOutput": adapt_out,
        "sloOutput": {
            "availability": ok_count / total_filtered,
            "p95LatencyMs": latencies[p95_index]
        }
    }
