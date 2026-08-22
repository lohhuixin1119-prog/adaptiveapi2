import base64
import json
import math
import os
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Adaptive API Gateway", version="2.0")


# ---------- Pydantic Response Schemas ----------

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


# ---------- Core Safe Business Logic ----------

def compute_adapt_output(adapt_input: dict) -> AdaptOutput:
    """Transforms adaptInput to adaptOutput safely, handling missing values and casing."""
    user = adapt_input.get("user") or {}
    metadata = adapt_input.get("metadata") or {}

    priority_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    
    # Clean input strings
    raw_priority = str(metadata.get("priority", "")).strip().upper()
    raw_action = str(adapt_input.get("action", "")).strip()

    return AdaptOutput(
        id=user.get("id"),
        name=user.get("fullName"),
        action=raw_action.lower(),
        priority=priority_map.get(raw_priority, 0)
    )


def compute_slo_output(heartbeats: list, slo_query: dict) -> SloOutput:
    """Calculates availability ratio and nearest-rank P95 latency."""
    target_service = str(slo_query.get("service", "")).strip()
    
    try:
        since_ts = float(slo_query.get("since", 0))
    except (ValueError, TypeError):
        since_ts = 0.0

    # Filter heartbeats with type safety
    relevant = []
    if isinstance(heartbeats, list):
        for hb in heartbeats:
            if isinstance(hb, dict) and str(hb.get("service", "")).strip() == target_service:
                try:
                    hb_ts = float(hb.get("timestamp", 0))
                    if hb_ts >= since_ts:
                        relevant.append(hb)
                except (ValueError, TypeError):
                    continue

    total = len(relevant)
    if total == 0:
        return SloOutput(availability=0.0, p95LatencyMs=0)

    # Calculate Availability
    ok_count = sum(
        1 for hb in relevant 
        if str(hb.get("status", "")).strip().upper() == "OK"
    )
    availability = ok_count / total

    # Calculate P95 Latency (Nearest Rank: ceil(0.95 * N) - 1)
    latencies = []
    for hb in relevant:
        try:
            latencies.append(int(hb.get("latencyMs", 0)))
        except (ValueError, TypeError):
            latencies.append(0)
            
    latencies.sort()
    
    # Nearest rank index formula clamped tightly between 0 and total - 1
    p95_index = math.ceil(0.95 * total) - 1
    clamped_index = max(0, min(p95_index, total - 1))
    p95 = latencies[clamped_index]

    return SloOutput(
        availability=round(availability, 4),
        p95LatencyMs=p95
    )


# ---------- Exception Handlers ----------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid request body structure"}
    )


# ---------- API Endpoints ----------

@app.post("/solve", response_model=SolveResponse)
async def solve(request: SolveRequest):
    try:
        # Clean Base64 string (Remove white spaces and newlines)
        payload_str = request.payload.strip().replace("\n", "").replace("\r", "")

        # Fix base64 padding if missing
        missing_padding = len(payload_str) % 4
        if missing_padding:
            payload_str += "=" * (4 - missing_padding)

        # Base64 Decode & JSON Parse
        decoded_bytes = base64.b64decode(payload_str)
        raw_json = json.loads(decoded_bytes.decode("utf-8"))

        adapt_input = raw_json.get("adaptInput") or {}
        heartbeats = raw_json.get("heartbeats") or []
        slo_query = raw_json.get("sloQuery") or {}

        # Compute Response Output
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
