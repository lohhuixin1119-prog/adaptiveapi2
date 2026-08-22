import base64
import json
import os
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

app = FastAPI(title="Adaptive API Gateway", version="2.0")


# ---------- Pydantic Models (input validation) ----------

class User(BaseModel):
    id: str = Field(..., description="User identifier")
    fullName: str = Field(..., description="User's full name")

    # Allow extra fields (if any) silently
    class Config:
        extra = "ignore"


class Metadata(BaseModel):
    priority: str = Field(..., description="Priority level: HIGH, MEDIUM, LOW")

    @validator("priority")
    def validate_priority(cls, v):
        if v not in {"HIGH", "MEDIUM", "LOW"}:
            raise ValueError("priority must be HIGH, MEDIUM, or LOW")
        return v

    class Config:
        extra = "ignore"


class AdaptInput(BaseModel):
    user: User
    action: str = Field(..., description="Action like CREATE, UPDATE, DELETE")
    metadata: Metadata

    class Config:
        extra = "ignore"


class Heartbeat(BaseModel):
    service: str = Field(..., description="Service name")
    timestamp: int = Field(..., description="Unix timestamp in seconds")
    latencyMs: int = Field(..., description="Latency in milliseconds")
    status: str = Field(..., description="OK or FAIL")

    @validator("status")
    def validate_status(cls, v):
        if v not in {"OK", "FAIL"}:
            raise ValueError("status must be OK or FAIL")
        return v

    class Config:
        extra = "ignore"


class SloQuery(BaseModel):
    service: str = Field(..., description="Service name to query")
    since: int = Field(..., description="Earliest timestamp to include")

    class Config:
        extra = "ignore"


class DecodedPayload(BaseModel):
    adaptInput: AdaptInput
    heartbeats: List[Heartbeat] = Field(default_factory=list)
    sloQuery: SloQuery

    class Config:
        extra = "ignore"


class SolveRequest(BaseModel):
    payload: str = Field(..., description="Base64-encoded JSON payload")


# ---------- Response models ----------

class AdaptOutput(BaseModel):
    id: str
    name: str
    action: str
    priority: int


class SloOutput(BaseModel):
    availability: float
    p95LatencyMs: int


class SolveResponse(BaseModel):
    adaptOutput: AdaptOutput
    sloOutput: SloOutput


# ---------- Exception handlers ----------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


# ---------- Core logic (split for testability) ----------

def compute_adapt_output(adapt_input: AdaptInput) -> AdaptOutput:
    """Transform adaptInput into adaptOutput per spec."""
    priority_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    return AdaptOutput(
        id=adapt_input.user.id,
        name=adapt_input.user.fullName,
        action=adapt_input.action.lower(),
        priority=priority_map.get(adapt_input.metadata.priority, 0),
    )


def compute_slo_output(heartbeats: List[Heartbeat], slo_query: SloQuery) -> SloOutput:
    """Calculate availability and p95 latency from filtered heartbeats."""
    # Filter heartbeats that match service and timestamp >= since
    relevant = [
        hb for hb in heartbeats
        if hb.service == slo_query.service and hb.timestamp >= slo_query.since
    ]

    total = len(relevant)
    if total == 0:
        return SloOutput(availability=0.0, p95LatencyMs=0)

    ok_count = sum(1 for hb in relevant if hb.status == "OK")
    availability = ok_count / total

    # Compute 95th percentile latency using sorted list (efficient for small arrays)
    latencies = sorted(hb.latencyMs for hb in relevant)
    # 95th percentile: index = ceil(0.95 * n) - 1 (0-based)
    idx = max(0, int(0.95 * total) - 1)
    p95 = latencies[min(idx, total - 1)]

    return SloOutput(availability=availability, p95LatencyMs=p95)


# ---------- Main endpoint ----------

@app.post("/solve", response_model=SolveResponse)
async def solve(request: SolveRequest):
    try:
        # 1. Decode base64
        try:
            decoded_bytes = base64.b64decode(request.payload)
            decoded_str = decoded_bytes.decode("utf-8")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 encoding")

        # 2. Parse JSON
        try:
            raw_json = json.loads(decoded_str)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in decoded payload")

        # 3. Validate and deserialize with Pydantic
        try:
            decoded = DecodedPayload(**raw_json)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # 4. Compute responses
        adapt_out = compute_adapt_output(decoded.adaptInput)
        slo_out = compute_slo_output(decoded.heartbeats, decoded.sloQuery)

        return SolveResponse(adaptOutput=adapt_out, sloOutput=slo_out)

    except HTTPException:
        raise
    except Exception as e:
        # Log the unexpected error (you can add proper logging here)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ---------- Health check (optional) ----------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------- Run with environment-aware port ----------

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=bool(os.getenv("DEV")))
