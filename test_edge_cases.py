import base64
import json
import requests

BASE = "http://localhost:8081/solve"


def call(obj):
    payload = base64.b64encode(json.dumps(obj).encode("utf-8")).decode("ascii")
    r = requests.post(BASE, json={"payload": payload})
    print(r.status_code, r.json())
    return r


print("1) Exact sample from prompt:")
call({
    "adaptInput": {
        "user": {"id": "U42", "fullName": "Jane Doe"},
        "action": "CREATE",
        "metadata": {"priority": "HIGH"},
    },
    "heartbeats": [
        {"service": "auth", "timestamp": 1710000123, "latencyMs": 120, "status": "OK"},
        {"service": "auth", "timestamp": 1710000125, "latencyMs": 180, "status": "FAIL"},
        {"service": "auth", "timestamp": 1710000121, "latencyMs": 95, "status": "OK"},
    ],
    "sloQuery": {"service": "auth", "since": 1710000123},
})
# expect adaptOutput == {id:U42, name:Jane Doe, action:create, priority:3}
# expect sloOutput == {availability:0.5, p95LatencyMs:180}

print("\n2) No matching heartbeats (wrong service):")
call({
    "adaptInput": {"user": {"id": "U1", "fullName": "Bob"}, "action": "DELETE", "metadata": {"priority": "LOW"}},
    "heartbeats": [{"service": "billing", "timestamp": 100, "latencyMs": 50, "status": "OK"}],
    "sloQuery": {"service": "auth", "since": 0},
})
# expect availability 0.0, p95LatencyMs 0

print("\n3) Missing metadata/priority entirely:")
call({
    "adaptInput": {"user": {"id": "U2", "fullName": "Amy"}, "action": "update"},
    "heartbeats": [],
    "sloQuery": {"service": "x", "since": 0},
})
# expect priority 0

print("\n4) Unknown priority value:")
call({
    "adaptInput": {"user": {"id": "U3", "fullName": "Eve"}, "action": "READ", "metadata": {"priority": "ULTRA"}},
    "heartbeats": [],
    "sloQuery": {"service": "x", "since": 0},
})
# expect priority 0 (unmapped)

print("\n5) All heartbeats OK -> availability 1.0:")
call({
    "adaptInput": {"user": {"id": "U4", "fullName": "Max"}, "action": "CREATE", "metadata": {"priority": "MEDIUM"}},
    "heartbeats": [
        {"service": "auth", "timestamp": 10, "latencyMs": 50, "status": "OK"},
        {"service": "auth", "timestamp": 20, "latencyMs": 60, "status": "OK"},
        {"service": "auth", "timestamp": 30, "latencyMs": 70, "status": "OK"},
    ],
    "sloQuery": {"service": "auth", "since": 0},
})
# expect availability 1.0, p95 of [50,60,70] sorted -> ceil(0.95*3)=3 -> 70

print("\n6) Single heartbeat:")
call({
    "adaptInput": {"user": {"id": "U5", "fullName": "Sam"}, "action": "CREATE"},
    "heartbeats": [{"service": "auth", "timestamp": 5, "latencyMs": 42, "status": "FAIL"}],
    "sloQuery": {"service": "auth", "since": 0},
})
# expect availability 0.0, p95LatencyMs 42

print("\n7) since boundary is inclusive:")
call({
    "adaptInput": {"user": {"id": "U6", "fullName": "Kim"}, "action": "CREATE"},
    "heartbeats": [{"service": "auth", "timestamp": 100, "latencyMs": 10, "status": "OK"}],
    "sloQuery": {"service": "auth", "since": 100},
})
# timestamp == since should be INCLUDED -> availability 1.0, p95 10
