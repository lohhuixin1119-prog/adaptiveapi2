from http.server import BaseHTTPRequestHandler, HTTPServer
import base64
import json
import math


HOST = "0.0.0.0"
PORT = 8000


PRIORITY_MAP = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3
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
        "priority": priority
    }


def percentile(values, percentile_value):
    """
    Nearest-rank percentile.

    For example:
    [120, 180] -> P95 = 180
    """

    if not values:
        return None

    values = sorted(values)

    rank = math.ceil(
        (percentile_value / 100) * len(values)
    )

    index = max(0, rank - 1)

    return values[index]


def calculate_slo(heartbeats, slo_query):
    service = slo_query.get("service")
    since = slo_query.get("since", 0)

    # Filter heartbeats
    filtered = [
        heartbeat
        for heartbeat in heartbeats
        if heartbeat.get("service") == service
        and heartbeat.get("timestamp", 0) >= since
    ]

    # No matching heartbeat
    if not filtered:
        return {
            "availability": 0,
            "p95LatencyMs": None
        }

    # Count successful heartbeats
    successful = sum(
        1
        for heartbeat in filtered
        if heartbeat.get("status") == "OK"
    )

    availability = successful / len(filtered)

    # Get latency values
    latencies = [
        heartbeat.get("latencyMs")
        for heartbeat in filtered
        if isinstance(
            heartbeat.get("latencyMs"),
            (int, float)
        )
    ]

    p95_latency = percentile(
        latencies,
        95
    )

    return {
        "availability": availability,
        "p95LatencyMs": p95_latency
    }


def solve(payload):
    # 1. Base64 decode
    decoded_bytes = base64.b64decode(payload)

    # 2. Convert bytes to string
    decoded_string = decoded_bytes.decode("utf-8")

    # 3. Parse JSON
    data = json.loads(decoded_string)

    # 4. Adapt input
    adapt_output = adapt_input(
        data.get("adaptInput", {})
    )

    # 5. Calculate SLO
    slo_output = calculate_slo(
        data.get("heartbeats", []),
        data.get("sloQuery", {})
    )

    # 6. Combine response
    return {
        "adaptOutput": adapt_output,
        "sloOutput": slo_output
    }


class SolveHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        # Only accept /solve
        if self.path != "/solve":
            self.send_response(404)
            self.send_header(
                "Content-Type",
                "application/json"
            )
            self.end_headers()

            response = {
                "error": "Not Found"
            }

            self.wfile.write(
                json.dumps(response).encode("utf-8")
            )

            return

        try:
            # Read request body
            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = self.rfile.read(
                content_length
            )

            # Parse request JSON
            request_data = json.loads(
                body.decode("utf-8")
            )

            # Get payload
            payload = request_data["payload"]

            # Solve
            result = solve(payload)

            # Convert result to JSON
            response = json.dumps(
                result
            ).encode("utf-8")

            # Send response
            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.send_header(
                "Content-Length",
                str(len(response))
            )

            self.end_headers()

            self.wfile.write(response)

        except Exception as e:

            response = json.dumps({
                "error": str(e)
            }).encode("utf-8")

            self.send_response(400)

            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.send_header(
                "Content-Length",
                str(len(response))
            )

            self.end_headers()

            self.wfile.write(response)


if __name__ == "__main__":

    server = HTTPServer(
        (HOST, PORT),
        SolveHandler
    )

    print(
        f"Server running on "
        f"http://localhost:{PORT}"
    )

    print(
        "POST requests to "
        f"http://localhost:{PORT}/solve"
    )

    server.serve_forever()
