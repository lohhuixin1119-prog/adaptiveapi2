import math
from typing import List
from schemas import Heartbeat, SloQuery, SloOutput

class SLOMetricsCalculator:
    """Computes Service Level Objectives (SLOs) from heartbeat time-series data."""

    @staticmethod
    def calculate(heartbeats: List[Heartbeat], query: SloQuery) -> SloOutput:
        # 1. Filter metrics based on the strict query parameters
        filtered = [
            hb for hb in heartbeats
            if hb.service == query.service and hb.timestamp >= query.since
        ]

        if not filtered:
            return SloOutput(availability=0.0, p95LatencyMs=0)

        # 2. Compute Availability (OK requests / Total valid requests)
        ok_count = sum(1 for hb in filtered if hb.status.upper() == "OK")
        availability = ok_count / len(filtered)

        # 3. Compute P95 Latency using the Nearest Rank method
        latencies = sorted(hb.latencyMs for hb in filtered)
        
        # P95 index = ceiling(0.95 * N) - 1 (0-indexed)
        p95_index = max(0, math.ceil(0.95 * len(latencies)) - 1)
        p95_latency = latencies[p95_index]

        return SloOutput(
            availability=round(availability, 4),
            p95LatencyMs=p95_latency
        )
