import base64
import json
import math
import logging
from flask import Flask, request, jsonify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)

PRIORITY_MAP = {
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1
}


def safe_base64_decode(encoded_str: str) -> dict:
    """Decodes base64 string safely, handling missing padding and JSON parsing."""
    if not encoded_str:
        return {}
    
    # Fix base64 padding if needed
    missing_padding = len(encoded_str) % 4
    if missing_padding:
        encoded_str += "=" * (4 - missing_padding)

    decoded_bytes = base64.b64decode(encoded_str)
    return json.loads(decoded_bytes.decode("utf-8"))


def process_adapt_input(adapt_input: dict) -> dict:
    """Processes V1 user/metadata into V2 adaptOutput schema."""
    user = adapt_input.get("user") or {}
    metadata = adapt_input.get("metadata") or {}
    
    raw_priority = str(metadata.get("priority", "")).upper()
    raw_action = str(adapt_input.get("action", ""))

    return {
        "id": user.get("id"),
        "name": user.get("fullName"),
        "action": raw_action.lower(),
        "priority": PRIORITY_MAP.get(raw_priority, 0)
    }


def process_slo_query(heartbeats: list, slo_query: dict) -> dict:
    """Calculates availability ratio and p95 latency for the queried service."""
    target_service = slo_query.get("service")
    since_timestamp = slo_query.get("since", 0)

    # Filter heartbeats matching service and timestamp >= since
    filtered = [
        hb for hb in heartbeats
        if isinstance(hb, dict) 
        and hb.get("service") == target_service 
        and hb.get("timestamp", 0) >= since_timestamp
    ]

    if not filtered:
        return {
            "availability": 0.0,
            "p95LatencyMs": 0
        }

    # Calculate Availability (Case-insensitive OK status match)
    ok_count = sum(1 for hb in filtered if str(hb.get("status", "")).upper() == "OK")
    availability = ok_count / len(filtered)

    # Calculate 95th Percentile Latency (Nearest-Rank Method)
    latencies = sorted(int(hb.get("latencyMs", 0)) for hb in filtered)
    n = len(latencies)
    
    # Rank index formula: ceil(0.95 * N) mapped to 0-indexed array
    rank = math.ceil(0.95 * n)
    p95_latency = latencies[max(0, rank - 1)]

    return {
        "availability": round(availability, 4),
        "p95LatencyMs": p95_latency
    }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/solve", methods=["POST"])
def solve():
    try:
        data = request.get_json(force=True, silent=True)
        if not data or "payload" not in data:
            return jsonify({"error": "Missing payload field"}), 400

        # Decode payload
        payload_data = safe_base64_decode(data["payload"])

        # Extract root components
        adapt_input = payload_data.get("adaptInput") or {}
        heartbeats = payload_data.get("heartbeats") or []
        slo_query = payload_data.get("sloQuery") or {}

        # Build output response
        response_data = {
            "adaptOutput": process_adapt_input(adapt_input),
            "sloOutput": process_slo_query(heartbeats, slo_query)
        }

        return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"Failed to process /solve request: {str(e)}")
        return jsonify({"error": "Invalid payload format"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
