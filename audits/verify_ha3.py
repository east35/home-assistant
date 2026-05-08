import requests, json
import websocket

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def ws_calls(messages):
    ws = websocket.create_connection("ws://192.168.4.179:8123/api/websocket", timeout=10)
    ws.recv()
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    assert json.loads(ws.recv())["type"] == "auth_ok"
    results = []
    for i, msg in enumerate(messages, start=1):
        msg["id"] = i
        ws.send(json.dumps(msg))
        results.append(json.loads(ws.recv()).get("result"))
    ws.close()
    return results

# ── 1. Get automation traces for Office J to see exact hue_event payload ──
traces_result, = ws_calls([
    {"type": "automation/trace/list", "automation_id": "1778266538824"}
])

print("=== Office J automation traces ===")
if traces_result:
    for t in traces_result[:3]:
        print(f"  run_id={t.get('run_id')} timestamp={t.get('timestamp')}")
    # Get full trace for most recent run
    latest_run_id = traces_result[0]["run_id"]
    trace_detail, = ws_calls([
        {"type": "automation/trace/get",
         "automation_id": "1778266538824",
         "run_id": latest_run_id}
    ])
    print(f"\nFull trace trigger context for run {latest_run_id}:")
    if trace_detail:
        trigger_vars = trace_detail.get("trace", {}).get("trigger", {})
        print(json.dumps(trigger_vars, indent=2))
        # Also look at variables at the top level
        variables = trace_detail.get("variables", {})
        trigger_var = variables.get("trigger", {})
        print("\nVariables > trigger:")
        print(json.dumps(trigger_var, indent=2))
else:
    print("  No traces found")

# ── 2. Check if hue_event is in the event registry (fired events) ──────────
print("\n\n=== Checking logbook for hue_event around last Office J trigger ===")
r = requests.get(
    f"{HA_URL}/api/logbook/2026-05-08T20:00:00+00:00",
    headers=HEADERS,
    params={"end_time": "2026-05-08T20:05:00+00:00"}
)
try:
    entries = r.json()
    for e in entries:
        if isinstance(e, dict):
            print(json.dumps(e))
except Exception as ex:
    print(f"Error: {ex} | raw: {r.text[:500]}")
