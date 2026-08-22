"""
Adaptive API Gateway Challenge

Implements POST /solve:

  Request:  { "payload": "<base64-encoded JSON>" }
  Payload decodes to: { adaptInput, heartbeats, sloQuery }
  Response: { adaptOutput, sloOutput }

--------------------------------------------------------------------------
adaptOutput  (V1 -> V2 adapter)
--------------------------------------------------------------------------
  id       <- adaptInput.user.id
  name     <- adaptInput.user.fullName
  action   <- adaptInput.action, lower-cased
  priority <- adaptInput.metadata.priority, mapped to an ordinal:
                LOW = 1, MEDIUM = 2, HIGH = 3, CRITICAL = 4
              unknown / missing priority -> 0

--------------------------------------------------------------------------
sloOutput (heartbeat health metrics)
--------------------------------------------------------------------------
  Filter heartbeats to: heartbeats[i].service == sloQuery.service
                         AND heartbeats[i].timestamp >= sloQuery.since

  availability  = (# filtered heartbeats with status == "OK") / (# filtered)
  p95LatencyMs  = 95th percentile of filtered latencyMs values, using the
                  nearest-rank method (ceil(p * n)-th smallest, 1-indexed).
                  This matches the worked example exactly:
                    filtered latencies (sorted) = [120, 180]
                    ceil(0.95 * 2) = 2 -> 2nd smallest = 180

  If no heartbeats match the filter, availability = 0.0 and
  p95LatencyMs = 0 (nothing to measure, reported as "no data" rather than
  raising an error).
"""

from __future__ import annotations

import base64
import binascii
import math
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Adaptive API Gateway")

PRIORITY_MAP = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


class SolveRequest(BaseModel):
    payload: str

    class Config:
        extra = "ignore"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _decode_payload(payload: str) -> dict[str, Any]:
    import json

    try:
        # Accept both standard and URL-safe base64, with or without padding.
        s = payload.strip()
        s += "=" * (-len(s) % 4)  # restore any missing padding
        try:
            raw = base64.b64decode(s, validate=False)
        except (binascii.Error, ValueError):
            raw = base64.urlsafe_b64decode(s)
        return json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc


def _build_adapt_output(adapt_input: dict[str, Any]) -> dict[str, Any]:
    user = adapt_input.get("user") or {}
    action_raw = adapt_input.get("action")
    metadata = adapt_input.get("metadata") or {}
    priority_raw = metadata.get("priority")

    priority = PRIORITY_MAP.get(str(priority_raw).upper(), 0) if priority_raw is not None else 0

    return {
        "id": user.get("id"),
        "name": user.get("fullName"),
        "action": str(action_raw).lower() if action_raw is not None else "",
        "priority": priority,
    }


def _nearest_rank_percentile(sorted_values: list[float], p: float) -> float:
    """Nearest-rank percentile: p in [0, 1]. 1-indexed ceil(p * n)."""
    n = len(sorted_values)
    if n == 0:
        return 0
    idx = math.ceil(p * n)
    idx = max(1, min(idx, n))
    return sorted_values[idx - 1]


def _build_slo_output(heartbeats: list[dict[str, Any]], slo_query: dict[str, Any]) -> dict[str, Any]:
    service = slo_query.get("service")
    since = slo_query.get("since", 0)

    filtered = [
        hb for hb in heartbeats
        if hb.get("service") == service and hb.get("timestamp", 0) >= since
    ]

    total = len(filtered)
    if total == 0:
        return {"availability": 0.0, "p95LatencyMs": 0}

    ok_count = sum(1 for hb in filtered if hb.get("status") == "OK")
    availability = ok_count / total

    latencies = sorted(hb.get("latencyMs", 0) for hb in filtered)
    p95 = _nearest_rank_percentile(latencies, 0.95)

    return {"availability": availability, "p95LatencyMs": p95}


# --------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------

@app.post("/solve")
def solve(req: SolveRequest) -> dict[str, Any]:
    decoded = _decode_payload(req.payload)

    adapt_input = decoded.get("adaptInput") or {}
    heartbeats = decoded.get("heartbeats") or []
    slo_query = decoded.get("sloQuery") or {}

    return {
        "adaptOutput": _build_adapt_output(adapt_input),
        "sloOutput": _build_slo_output(heartbeats, slo_query),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
