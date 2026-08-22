import base64
import json
import math
import logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)

PRIORITY_MAP = {
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1
}


def process_adapt_input(adapt_input):
    user = adapt_input.get("user", {})
    metadata = adapt_input.get("metadata", {})
    priority_str = metadata.get("priority", "").upper()

    return {
        "id": user.get("id"),
        "name": user.get("fullName"),
        "action": adapt_input.get("action", "").lower(),
        "priority": PRIORITY_MAP.get(priority_str, 0)
    }


def process_slo_query(heartbeats, slo_query):
    target_service = slo_query.get("service")
    since_timestamp = slo_query.get("since")

    # Filter heartbeats matching service and timestamp >= since
    filtered = [
        hb for hb in heartbeats
        if hb.get("service") == target_service and hb.get("timestamp", 0) >= since_timestamp
    ]

    if not filtered:
        return {
            "availability": 0.0,
            "p95LatencyMs": 0
        }

    # Availability ratio: OK statuses / total filtered heartbeats
    ok_count = sum(1 for hb in filtered if hb.get("status") == "OK")
    availability = ok_count / len(filtered)

    # 95th Percentile Latency (Nearest Rank method)
    latencies = sorted([hb.get("latencyMs", 0) for hb in filtered])
    n = len(latencies)
    rank = math.ceil(0.95 * n)
    p95_latency = latencies[max(0, rank - 1)]

    return {
        "availability": availability,
        "p95LatencyMs": p95_latency
    }


@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.get_json(force=True)
        encoded_payload = data.get("payload", "")

        decoded_bytes = base64.b64decode(encoded_payload)
        payload_data = json.loads(decoded_bytes.decode('utf-8'))

        adapt_input = payload_data.get("adaptInput", {})
        heartbeats = payload_data.get("heartbeats", [])
        slo_query = payload_data.get("sloQuery", {})

        adapt_output = process_adapt_input(adapt_input)
        slo_output = process_slo_query(heartbeats, slo_query)

        return jsonify({
            "adaptOutput": adapt_output,
            "sloOutput": slo_output
        }), 200

    except Exception as e:
        logging.error(f"Error processing /solve payload: {str(e)}")
        return jsonify({"error": "Invalid payload format"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
