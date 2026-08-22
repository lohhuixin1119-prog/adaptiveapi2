from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import json
import math


# ==========================================
# Create FastAPI application
# ==========================================

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
# Home / Health Check
# ==========================================

@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "Adaptive API Gateway is running"
    }


# ==========================================
# Adapt V1 input -> V2 output
# ==========================================

def adapt_input(adapt_input_data):

    user = adapt_input_data.get("user", {})
    metadata = adapt_input_data.get("metadata", {})

    # Get action
    action = adapt_input_data.get("action")

    if action is not None:
        action = action.lower()

    # Get priority
    priority = metadata.get("priority")

    if isinstance(priority, str):
        priority = PRIORITY_MAP.get(
            priority.upper()
        )

    return {
        "id": user.get("id"),
        "name": user.get("fullName"),
        "action": action,
        "priority": priority
    }


# ==========================================
# P95 calculation
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
# SLO calculation
# ==========================================

def calculate_slo(heartbeats, slo_query):

    service = slo_query.get("service")
    since = slo_query.get("since", 0)

    # --------------------------------------
    # Filter heartbeat records
    # --------------------------------------

    filtered_heartbeats = [
        heartbeat
        for heartbeat in heartbeats
        if heartbeat.get("service") == service
        and heartbeat.get("timestamp", 0) >= since
    ]

    # --------------------------------------
    # No matching data
    # --------------------------------------

    if not filtered_heartbeats:
        return {
            "availability": 0,
            "p95LatencyMs": None
        }

    # --------------------------------------
    # Calculate availability
    # --------------------------------------

    successful_count = sum(
        1
        for heartbeat in filtered_heartbeats
        if heartbeat.get("status") == "OK"
    )

    total_count = len(
        filtered_heartbeats
    )

    availability = (
        successful_count / total_count
    )

    # --------------------------------------
    # Get latency values
    # --------------------------------------

    latencies = [
        heartbeat.get("latencyMs")
        for heartbeat in filtered_heartbeats
        if isinstance(
            heartbeat.get("latencyMs"),
            (int, float)
        )
    ]

    # --------------------------------------
    # Calculate P95
    # --------------------------------------

    p95_latency = calculate_p95(
        latencies
    )

    return {
        "availability": availability,
        "p95LatencyMs": p95_latency
    }


# ==========================================
# POST /solve
# ==========================================

@app.post("/solve")
def solve(request: SolveRequest):

    try:

        # ----------------------------------
        # 1. Get Base64 payload
        # ----------------------------------

        encoded_payload = request.payload

        # ----------------------------------
        # 2. Decode Base64
        # ----------------------------------

        decoded_bytes = base64.b64decode(
            encoded_payload
        )

        # ----------------------------------
        # 3. Convert bytes -> string
        # ----------------------------------

        decoded_string = decoded_bytes.decode(
            "utf-8"
        )

        # ----------------------------------
        # 4. Parse JSON
        # ----------------------------------

        data = json.loads(
            decoded_string
        )

        # ----------------------------------
        # 5. Get input data
        # ----------------------------------

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

        # ----------------------------------
        # 6. Generate adaptOutput
        # ----------------------------------

        adapt_output = adapt_input(
            adapt_input_data
        )

        # ----------------------------------
        # 7. Generate sloOutput
        # ----------------------------------

        slo_output = calculate_slo(
            heartbeats,
            slo_query
        )

        # ----------------------------------
        # 8. Return combined response
        # ----------------------------------

        return {
            "adaptOutput": adapt_output,
            "sloOutput": slo_output
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Invalid payload: {str(e)}"
        )
