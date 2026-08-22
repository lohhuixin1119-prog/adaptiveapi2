from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import binascii
import json
import math
import os


app = FastAPI()


# ==========================================
# Request model
# ==========================================

class SolveRequest(BaseModel):
    payload: str


# ==========================================
# Priority mapping
# ==========================================

PRIORITY_MAP = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3
}


# ==========================================
# Health check
# ==========================================

@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "Adaptive API Gateway is running"
    }


# ==========================================
# Adapt input
# ==========================================

def adapt_input(data):
    user = data.get("user") or {}
    metadata = data.get("metadata") or {}

    # User ID
    user_id = user.get("id")

    # Full name
    name = user.get("fullName")

    # Action
    action = data.get("action")

    if isinstance(action, str):
        action = action.lower()

    # Priority
    priority = metadata.get("priority")

    if isinstance(priority, str):
        priority = PRIORITY_MAP.get(
            priority.upper()
        )

    return {
        "id": user_id,
        "name": name,
        "action": action,
        "priority": priority
    }


# ==========================================
# P95
# ==========================================

def calculate_p95(values):

    if not values:
        return None

    values = sorted(values)

    # Nearest-rank percentile
    rank = math.ceil(
        0.95 * len(values)
    )

    index = max(
        0,
        rank - 1
    )

    return values[index]


# ==========================================
# SLO
# ==========================================

def calculate_slo(heartbeats, query):

    service = query.get("service")
    since = query.get("since")

    # If since is missing, consider all timestamps
    if since is None:
        since = float("-inf")

    # --------------------------------------
    # Filter heartbeat records
    # --------------------------------------

    filtered = []

    for heartbeat in heartbeats:

        if not isinstance(heartbeat, dict):
            continue

        heartbeat_service = heartbeat.get(
            "service"
        )

        timestamp = heartbeat.get(
            "timestamp"
        )

        if heartbeat_service != service:
            continue

        if not isinstance(
            timestamp,
            (int, float)
        ):
            continue

        if timestamp < since:
            continue

        filtered.append(
            heartbeat
        )

    # --------------------------------------
    # No data
    # --------------------------------------

    if not filtered:
        return {
            "availability": 0,
            "p95LatencyMs": None
        }

    # --------------------------------------
    # Availability
    # --------------------------------------

    ok_count = sum(
        1
        for heartbeat in filtered
        if heartbeat.get("status") == "OK"
    )

    availability = (
        ok_count / len(filtered)
    )

    # --------------------------------------
    # Latencies
    # --------------------------------------

    latencies = []

    for heartbeat in filtered:

        latency = heartbeat.get(
            "latencyMs"
        )

        if isinstance(
            latency,
            (int, float)
        ):
            latencies.append(
                latency
            )

    # --------------------------------------
    # P95
    # --------------------------------------

    p95_latency = calculate_p95(
        latencies
    )

    return {
        "availability": availability,
        "p95LatencyMs": p95_latency
    }


# ==========================================
# Solve
# ==========================================

@app.post("/solve")
def solve(request: SolveRequest):

    # --------------------------------------
    # Validate payload
    # --------------------------------------

    if not request.payload:
        raise HTTPException(
            status_code=400,
            detail="Missing payload"
        )

    try:

        # ----------------------------------
        # Base64 decode
        # ----------------------------------

        decoded_bytes = base64.b64decode(
            request.payload,
            validate=True
        )

    except (
        binascii.Error,
        ValueError
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid Base64 payload"
        )

    # --------------------------------------
    # Decode UTF-8
    # --------------------------------------

    try:

        decoded_text = decoded_bytes.decode(
            "utf-8"
        )

    except UnicodeDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Payload is not valid UTF-8"
        )

    # --------------------------------------
    # Parse JSON
    # --------------------------------------

    try:

        data = json.loads(
            decoded_text
        )

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Decoded payload is not valid JSON"
        )

    # --------------------------------------
    # Validate root object
    # --------------------------------------

    if not isinstance(data, dict):

        raise HTTPException(
            status_code=400,
            detail="Decoded payload must be a JSON object"
        )

    # --------------------------------------
    # Extract sections
    # --------------------------------------

    adapt_input_data = data.get(
        "adaptInput",
        {}
    )

    heartbeats = data.get(
        "heartbeats",
        []
    )

    slo_query = data.get(
        "sloQuery",
        {}
    )

    if not isinstance(
        adapt_input_data,
        dict
    ):
        raise HTTPException(
            status_code=400,
            detail="adaptInput must be an object"
        )

    if not isinstance(
        heartbeats,
        list
    ):
        raise HTTPException(
            status_code=400,
            detail="heartbeats must be an array"
        )

    if not isinstance(
        slo_query,
        dict
    ):
        raise HTTPException(
            status_code=400,
            detail="sloQuery must be an object"
        )

    # --------------------------------------
    # Generate outputs
    # --------------------------------------

    adapt_output = adapt_input(
        adapt_input_data
    )

    slo_output = calculate_slo(
        heartbeats,
        slo_query
    )

    # --------------------------------------
    # Final response
    # --------------------------------------

    return {
        "adaptOutput": adapt_output,
        "sloOutput": slo_output
    }


# ==========================================
# Local development
# ==========================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.environ.get(
            "PORT",
            8000
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
