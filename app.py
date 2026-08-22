from flask import Flask, request, jsonify
import base64
import json

app = Flask(__name__)

@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.get_json()
        if not data or 'payload' not in data:
            return jsonify({'error': 'Missing "payload" field'}), 400

        payload = data['payload']
        if not isinstance(payload, str):
            return jsonify({'error': 'Payload must be a string'}), 400

        # Decode base64
        try:
            decoded_bytes = base64.b64decode(payload)
            decoded_str = decoded_bytes.decode('utf-8')
        except Exception:
            return jsonify({'error': 'Invalid base64 encoding'}), 400

        # Parse JSON
        try:
            input_data = json.loads(decoded_str)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON in decoded payload'}), 400

        adapt_input = input_data.get('adaptInput')
        heartbeats = input_data.get('heartbeats', [])
        slo_query = input_data.get('sloQuery')

        if not adapt_input or not slo_query:
            return jsonify({'error': 'Missing adaptInput or sloQuery'}), 400

        # Build adaptOutput
        priority_map = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        user = adapt_input.get('user', {})
        metadata = adapt_input.get('metadata', {})
        adapt_output = {
            'id': user.get('id', ''),
            'name': user.get('fullName', ''),
            'action': adapt_input.get('action', '').lower(),
            'priority': priority_map.get(metadata.get('priority'), 0)
        }

        # Compute SLO metrics
        service = slo_query.get('service')
        since = slo_query.get('since')
        relevant = [
            hb for hb in heartbeats
            if hb.get('service') == service and hb.get('timestamp', 0) >= since
        ]

        total = len(relevant)
        availability = 0.0
        p95_latency_ms = 0

        if total > 0:
            ok_count = sum(1 for hb in relevant if hb.get('status') == 'OK')
            availability = ok_count / total

            latencies = sorted(hb.get('latencyMs', 0) for hb in relevant)
            index = int(0.95 * total) - 1  # 0-based index for 95th percentile
            if index < 0:
                index = 0
            p95_latency_ms = latencies[min(index, total - 1)]

        slo_output = {
            'availability': availability,
            'p95LatencyMs': p95_latency_ms
        }

        return jsonify({
            'adaptOutput': adapt_output,
            'sloOutput': slo_output
        })

    except Exception as e:
        app.logger.error(f'Unexpected error: {e}')
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
