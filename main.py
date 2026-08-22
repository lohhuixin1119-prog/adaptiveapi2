import base64
import json
import math
import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Adaptive API Gateway", version="2.0")


class SolveRequest(BaseModel):
    payload: str = Field(..., description="Base64-encoded JSON payload")


def safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def calculate_p95(latencies: List[int]) -> int:
    """Calculates 95th percentile with linear interpolation/nearest rank safety."""
    n = len(latencies)
    if n == 0:
        return 0
    if n == 1:
        return latencies[0]

    # Standard Nearest Rank method
    rank = math.ceil(0.95 * n) - 1
    rank = max(0, min(rank, n - 1))
    return latencies[rank]


def compute_adapt_output(adapt_input: Any) -> Dict[str, Any]:
    if not isinstance(adapt_input, dict):
        adapt_input = {}

    user = adapt_input.get("user")
    if not isinstance(user, dict):
        user = {}

    metadata = adapt_input.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    priority_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    raw_priority = str(metadata.get("priority", "")).strip().upper()
    priority_val = priority_map.get(raw_priority, 0)

    raw_action = adapt_input.get("action")
    action_val = str(raw_action).strip().lower() if raw_action is not None else ""

    return {
        "id": user.get("id"),
        "name": user.get("fullName"),
        "action": action_val,
        "priority": priority_val
    }


def compute_slo_output(heartbeats: Any, slo_query: Any) -> Dict[str, Any]:
    if not isinstance(slo_query, dict):
        slo_query = {}
    if not isinstance(heartbeats, list):
        heartbeats = []

    target_service = str(slo_query.get("service", "")).strip()
    since_ts = safe_float(slo_query.get("since", 0))

    relevant = []
    for hb in heartbeats:
        if isinstance(hb, dict):
            hb_service = str(hb.get("service", "")).strip()
            if hb_service == target_service:
                hb_ts = safe_float(hb.get("timestamp", 0))
                if hb_ts >= since_ts:
                    relevant.append(hb)

    total = len(relevant)
    if total == 0:
        return {
            "availability": 0.0,
            "p95LatencyMs": 0
        }

    # Calculate Availability
    ok_count = 0
    latencies = []
    for hb in relevant:
        status_str = str(hb.get("status", "")).strip().upper()
        if status_str == "OK":
            ok_count += 1
        latencies.append(safe_int(hb.get("latencyMs", 0)))

    availability = ok_count / total
    latencies.sort()
    p95_val = calculate_p95(latencies)

    return {
        "availability": round(availability, 6),
        "p95LatencyMs": p95_val
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid payload format"}
    )


@app.post("/solve")
async def solve(request: SolveRequest):
    try:
        payload_str = request.payload.strip().replace("\n", "").replace("\r", "")
        
        # Add missing base64 padding
        missing_padding = len(payload_str) % 4
        if missing_padding:
            payload_str += "=" * (4 - missing_padding)

        # Decode base64
        decoded_bytes = base64.b64decode(payload_str)
        decoded_str = decoded_bytes.decode("utf-8")
        
        # Parse JSON
        raw_json = json.loads(decoded_str)
        if not isinstance(raw_json, dict):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Decoded payload is not a JSON object"}
            )

        adapt_input = raw_json.get("adaptInput")
        heartbeats = raw_json.get("heartbeats")
        slo_query = raw_json.get("sloQuery")

        adapt_out = compute_adapt_output(adapt_input)
        slo_out = compute_slo_output(heartbeats, slo_query)

        return {
            "adaptOutput": adapt_out,
            "sloOutput": slo_out
        }

    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid or malformed base64 payload"}
        )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
