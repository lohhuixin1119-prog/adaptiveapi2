from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64, json

app = FastAPI()

class SolveRequest(BaseModel):
    payload: str

@app.post("/solve")
async def solve(request: SolveRequest):
    try:
        raw = request.payload
        if not raw:
            raise HTTPException(400, "Missing payload")
        try:
            decoded = base64.b64decode(raw).decode('utf-8')
        except:
            raise HTTPException(400, "Invalid base64")
        try:
            data = json.loads(decoded)
        except:
            raise HTTPException(400, "Invalid JSON")

        adapt_input = data.get('adaptInput')
        heartbeats = data.get('heartbeats', [])
        slo_query = data.get('sloQuery')
        if not adapt_input or not slo_query:
            raise HTTPException(400, "Missing adaptInput or sloQuery")

        priority_map = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        user = adapt_input.get('user', {})
        meta = adapt_input.get('metadata', {})
        adapt_output = {
            'id': user.get('id', ''),
            'name': user.get('fullName', ''),
            'action': adapt_input.get('action', '').lower(),
            'priority': priority_map.get(meta.get('priority'), 0)
        }

        service = slo_query.get('service')
        since = slo_query.get('since')
        relevant = [h for h in heartbeats if h.get('service') == service and h.get('timestamp', 0) >= since]
        total = len(relevant)
        availability = 0.0
        p95 = 0
        if total:
            ok = sum(1 for h in relevant if h.get('status') == 'OK')
            availability = ok / total
            lat = sorted(h.get('latencyMs', 0) for h in relevant)
            idx = max(0, int(0.95 * total) - 1)
            p95 = lat[min(idx, total - 1)]
        slo_output = {'availability': availability, 'p95LatencyMs': p95}
        return {'adaptOutput': adapt_output, 'sloOutput': slo_output}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Internal error: {e}")
