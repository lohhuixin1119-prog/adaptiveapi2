import base64
import json
import math
import os
from typing import List, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Adaptive API Gateway", version="2.0")


# ---------- Pydantic Input/Output Schemas ----------

class SolveRequest(BaseModel):
    payload: str = Field(..., description="Base64-encoded JSON payload")


class AdaptOutput(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    action: str
    priority: int


class SloOutput(BaseModel):
    availability: float
    p95LatencyMs: int


class SolveResponse(BaseModel):
    adaptOutput: AdaptOutput
    sloOutput: SloOutput


# ---------- Core Computation Functions ----------

def compute_adapt_output(adapt_input: dict) -> AdaptOutput:
    """Transforms adaptInput to adaptOutput safely without throwing validation errors."""
    user = adapt_input.get("user") or {}
    metadata = adapt_input.get("metadata") or {}

    priority_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    raw_priority = str(metadata.get("priority", "")).upper()
    raw_action = str(adapt_input.get("action", ""))

    return AdaptOutput(
        id=user.get("id"),
        name=user.get("fullName"),
        action=raw_action.lower(),
        priority=priority_map.get(raw_priority, 0)
    )


def compute_slo_output(heartbeats: list, slo_query: dict) -> SloOutput:
    """Calculates availability and p95 latency using nearest-rank index logic."""
    target_service = slo_query.get("service")
    since_ts = slo_query.get("since", 0)

    # Filter heartbeats matching target service and timestamp >= since
    relevant = [
        hb for hb in heartbeats
        if isinstance(hb, dict)
        and hb.get("service") == target_service
        and hb.get("timestamp", 0) >= since_ts
    ]

    total = len(relevant)
    if total == 0:
        return SloOutput(availability=0.0, p95LatencyMs=0)

    # Availability (Case-insensitive status check)
    ok_count = sum(1 for hb in relevant if str(hb.get("status", "")).upper() == "OK")
    availability = ok_count / total

    # P95 Latency using Nearest Rank: index = ceil(0.95 * N) - 1
    latencies = sorted(int(hb.get("latencyMs", 0)) for hb in relevant)
    p95_index = math.ceil(0.95 * total) - 1
    p95 = latencies[max(0, min(p95_index, total - 1))]

    return SloOutput(
        availability=round(availability, 4),
        p95LatencyMs=p95
    )


# ---------- Endpoints & Handlers ----------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid request body structure"}
    )


@app.post("/solve", response_model=SolveResponse)
async def solve(request: SolveRequest):
    try:
        payload_str = request.payload

        # Fix base64 missing padding
        missing_padding = len(payload_str) % 4
        if missing_padding:
            payload_str += "=" * (4 - missing_padding)

        # Base64 Decode & JSON Parse
        decoded_bytes = base64.b64decode(payload_str)
        raw_json = json.loads(decoded_bytes.decode("utf-8"))

        adapt_input = raw_json.get("adaptInput") or {}
        heartbeats = raw_json.get("heartbeats") or []
        slo_query = raw_json.get("sloQuery") or {}

        # Compute output JSON
        adapt_out = compute_adapt_output(adapt_input)
        slo_out = compute_slo_output(heartbeats, slo_query)

        return SolveResponse(adaptOutput=adapt_out, sloOutput=slo_out)

    except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Malformed payload or JSON structure"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Internal server error: {str(e)}"}
        )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
