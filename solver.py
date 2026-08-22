"""
Adaptive API Gateway Challenge - Core Logic (Python)
"""
import base64
import json
import math
from typing import Any, Dict
def decode_payload(req_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decodes payload from request body.
    Handles Base64 encoded strings, raw JSON strings, or direct dict objects.
    """
    if not isinstance(req_body, dict):
        return {}
    raw_payload = req_body.get('payload', req_body)
    if isinstance(raw_payload, str):
        # 1. Try decoding Base64 first
        try:
            decoded_bytes = base64.b64decode(raw_payload)
            decoded_str = decoded_bytes.decode('utf-8')
            parsed = json.loads(decoded_str)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        # 2. Try direct JSON parsing
        try:
            parsed = json.loads(raw_payload)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    elif isinstance(raw_payload, dict):
        return raw_payload
    return {}
def parse_priority(pri: Any) -> int:
    """
    Maps priority strings/numbers to standard integer priority.
    LOW -> 1
    MEDIUM/MED -> 2
    HIGH -> 3
    CRITICAL/URGENT -> 4
    """
    if pri is None:
        return 0
    if isinstance(pri, (int, float)):
        return int(pri)
    pri_str = str(pri).strip().upper()
    if pri_str in ('LOW', '1'):
        return 1
    if pri_str in ('MEDIUM', 'MED', 'NORMAL', '2'):
        return 2
    if pri_str in ('HIGH', '3'):
        return 3
    if pri_str in ('CRITICAL', 'URGENT', '4'):
        return 4
    try:
        return int(pri_str)
    except ValueError:
        return 0
def solve_challenge(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes adaptInput, heartbeats, and sloQuery to construct response.
    Returns:
    {
        "adaptOutput": {
            "id": str,
            "name": str,
            "action": str,
            "priority": int
        },
        "sloOutput": {
            "availability": float,
            "p95LatencyMs": int/float
        }
    }
    """
    adapt_input = data.get('adaptInput') or {}
    heartbeats = data.get('heartbeats') or []
    if not isinstance(heartbeats, list):
        heartbeats = []
    slo_query = data.get('sloQuery') or {}
    # --- 1. Transform adaptInput -> adaptOutput ---
    user = adapt_input.get('user') or {}
    metadata = adapt_input.get('metadata') or {}
    user_id = (
        user.get('id')
        or user.get('userId')
        or adapt_input.get('id')
        or adapt_input.get('userId')
        or ''
    )
    name = (
        user.get('fullName')
        or user.get('name')
        or adapt_input.get('fullName')
        or adapt_input.get('name')
        or ''
    )
    action = str(adapt_input.get('action') or '').lower()
    raw_priority = metadata.get('priority') if 'priority' in metadata else adapt_input.get('priority')
    priority = parse_priority(raw_priority)
    adapt_output = {
        'id': user_id,
        'name': name,
        'action': action,
        'priority': priority
    }
    # --- 2. Compute SLO metrics -> sloOutput ---
    target_service = slo_query.get('service')
    since_timestamp = slo_query.get('since')
    filtered_hb = []
    for hb in heartbeats:
        if not isinstance(hb, dict):
            continue
        # Service match filter
        if target_service is not None and target_service != '':
            if hb.get('service') != target_service:
                continue
        # Timestamp match filter (since is inclusive: timestamp >= since)
        if since_timestamp is not None:
            hb_ts = hb.get('timestamp')
            if isinstance(hb_ts, (int, float)) and hb_ts < since_timestamp:
                continue
        filtered_hb.append(hb)
    availability = 0.0
    p95_latency_ms = 0
    if filtered_hb:
        # Count "OK" status
        ok_count = sum(
            1 for hb in filtered_hb if str(hb.get('status', '')).upper() == 'OK'
        )
        availability = ok_count / len(filtered_hb)
        # Extract latencies
        latencies = []
        for hb in filtered_hb:
            lat = hb.get('latencyMs')
            if lat is not None:
                try:
                    latencies.append(float(lat))
                except (ValueError, TypeError):
                    pass
        latencies.sort()
        if latencies:
            # Nearest-rank 95th percentile index: max(0, ceil(0.95 * N) - 1)
            p95_idx = max(0, math.ceil(0.95 * len(latencies)) - 1)
            p95_val = latencies[p95_idx]
            p95_latency_ms = int(p95_val) if p95_val.is_integer() else p95_val
    return {
        'adaptOutput': adapt_output,
        'sloOutput': {
            'availability': availability,
            'p95LatencyMs': p95_latency_ms
        }
    }
