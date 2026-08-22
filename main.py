from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import json
import math

app = FastAPI()


class SolveRequest(BaseModel):
    payload: str


PRIORITY_MAP = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


def adapt_input(adapt_input):
    user = adapt_input.get("user", {})
    metadata = adapt_input.get("metadata", {})

    action = adapt_input.get("action")
    if action is not None:
        action = action.lower()

    priority = metadata.get("priority")
    if isinstance(priority, str):
        priority = PRIORITY_MAP.get(priority.upper())

    return {
        "id": user.get("id"),
        "name": user.get("fullName"),
        "action": action,
        "priority": priority,
    }


def percentile(values, percentile_value):
    """Nearest-rank percentile. P95 of [120, 180] is 180."""
    if not values:
        return None

    values = sorted(values)
    rank = math.ceil((percentile_value / 100) * len(values))
    index = max(0, rank - 1)

    return values[index]


def calculate_slo(heartbeats, slo_query):
    service = slo_query.get("service")
    since = slo_query.get("since", 0)

    filtered = [
        heartbeat
        for heartbeat in heartbeats
        if heartbeat.get("service") == service
        and heartbeat.get("timestamp", 0) >= since
    ]

    if not filtered:
        return {
            "availability": 0,
            "p95LatencyMs": None,
        }

    successful = sum(
        1 for heartbeat in filtered
        if heartbeat.get("status") == "OK"
    )

    availability = successful / len(filtered)

    latencies = [
        heartbeat.get("latencyMs")
        for heartbeat in filtered
        if isinstance(heartbeat.get("latencyMs"), (int, float))
    ]

    return {
        "availability": availability,
        "p95LatencyMs": percentile(latencies, 95),
    }


@app.post("/solve")
def solve(request: SolveRequest):
    try:
        decoded_bytes = base64.b64decode(request.payload)
        decoded_string = decoded_bytes.decode("utf-8")
        data = json.loads(decoded_string)

        adapt_output = adapt_input(
            data.get("adaptInput", {})
        )

        slo_output = calculate_slo(
            data.get("heartbeats", []),
            data.get("sloQuery", {}),
        )

        return {
            "adaptOutput": adapt_output,
            "sloOutput": slo_output,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payload: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
