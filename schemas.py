from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Incoming Request Model ---
class EncodedPayloadRequest(BaseModel):
    payload: str = Field(..., description="Base64 encoded JSON string")

# --- Decoded V1 Input Models ---
class UserV1(BaseModel):
    id: str
    fullName: str

class AdaptInputV1(BaseModel):
    user: UserV1
    action: str
    metadata: Dict[str, Any]

class Heartbeat(BaseModel):
    service: str
    timestamp: int
    latencyMs: int
    status: str

class SloQuery(BaseModel):
    service: str
    since: int

class DecodedPayload(BaseModel):
    adaptInput: AdaptInputV1
    heartbeats: List[Heartbeat]
    sloQuery: SloQuery

# --- Outgoing V2 Output Models ---
class AdaptOutputV2(BaseModel):
    id: str
    name: str
    action: str
    priority: int

class SloOutput(BaseModel):
    availability: float
    p95LatencyMs: int

class SolveResponse(BaseModel):
    adaptOutput: AdaptOutputV2
    sloOutput: SloOutput
