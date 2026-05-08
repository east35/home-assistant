import requests
import json
from collections import defaultdict

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def get(path):
    return requests.get(f"{HA_URL}{path}", headers=HEADERS).json()

def post(path, body):
    return requests.post(f"{HA_URL}{path}", headers=HEADERS, json=body).text

def ws_query(msg_type, extra=None):
    """Use websocket to query HA (entity registry, device registry, etc.)"""
    import websocket, json, os
    results = {}
    ws = websocket.create_connection(f"ws://192.168.4.179:8123/api/websocket", timeout=10)
    # auth
    ws.recv()  # auth_required
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    auth_result = json.loads(ws.recv())
    if auth_result.get("type") != "auth_ok":
        raise Exception(f"Auth failed: {auth_result}")
    payload = {"id": 1, "type": msg_type}
    if extra:
        payload.update(extra)
    ws.send(json.dumps(payload))
    resp = json.loads(ws.recv())
    ws.close()
    return resp.get("result", [])

# ── 1. All states ──────────────────────────────────────────────────────────
states = get("/api/states")
scenes = {e["entity_id"]: e for e in states if e["entity_id"].startswith("scene.")}
lights = {e["entity_id"]: e for e in states if e["entity_id"].startswith("light.")}

# ── 2. Rooms with all 4 required scenes ───────────────────────────────────
REQUIRED = {"cool_bright", "relax", "rest", "nightlight"}
room_scenes = defaultdict(set)
for sid in scenes:
    name = sid[len("scene."):]
    for suffix in REQUIRED:
        if name.endswith(f"_{suffix}"):
            room = name[: -len(suffix) - 1]
            room_scenes[room].add(suffix)

complete_rooms = sorted(r for r, s in room_scenes.items() if REQUIRED.issubset(s))
print("=== Rooms with all 4 scenes ===")
for r in complete_rooms:
    print(f"  {r}")

# ── 3. Entity registry via WebSocket ──────────────────────────────────────
print("\n=== Fetching entity registry via WebSocket ===")
try:
    import websocket
    entity_registry = ws_query("config/entity_registry/list")
    print(f"  Got {len(entity_registry)} entries")

    # Find unique_ids for Hue switch button event entities
    switch_entries = [
        e for e in entity_registry
        if e.get("entity_id", "").startswith("event.")
        and "switch" in e.get("original_name", "").lower()
        and "button" in e.get("original_name", "").lower()
    ]
    print("\n=== Switch button unique_ids ===")
    for e in switch_entries:
        print(f"  {e['entity_id']}")
        print(f"    unique_id : {e.get('unique_id', '?')}")
        print(f"    name      : {e.get('original_name', '?')}")

except ImportError:
    print("  websocket-client not installed, falling back to template API")
    entity_registry = None

# ── 4. Device registry via WebSocket ──────────────────────────────────────
if entity_registry is not None:
    print("\n=== Fetching device registry via WebSocket ===")
    device_registry = ws_query("config/device_registry/list")
    hue_switches = [
        d for d in device_registry
        if "switch" in (d.get("name") or "").lower()
        and any(i[0] == "hue" for i in (d.get("identifiers") or []))
    ]
    print("Hue switch devices:")
    for d in hue_switches:
        print(f"  id={d['id']} name={d.get('name')} name_by_user={d.get('name_by_user')}")
        print(f"    identifiers: {d.get('identifiers')}")

# ── 5. Verify planned light entities ──────────────────────────────────────
print("\n=== Light entity verification ===")
planned_lights = {
    "guest_bathroom": "light.guest_bathroom",
    "hallway_garage": "light.hallway_garage",
    "kitchen_recessed": "light.kitchen",
    "office_m": "light.office_m_2",
    "primary_bathroom": "light.primary_bathroom",
}
for room, eid in planned_lights.items():
    found = eid in lights
    fn = lights[eid]["attributes"].get("friendly_name", "") if found else "NOT FOUND"
    print(f"  {room}: {eid} -> {'✓' if found else '✗'} {fn}")

# ── 6. Check template API for hue_event id derivation ─────────────────────
print("\n=== hue_event id check via template ===")
device_ids = {
    "Office Switch - J":        "14a947fa6612ce3fe1e1a014acac72e8",
    "Bathroom Switch - Guest":  "b42505161ebee80abf332ccdaea30335",
    "Office Switch - M":        "da1bbbf2a672ddc65db37642370cdc04",
    "Bathroom Switch - Primary":"571ba26928a5c6382786d7d89b95c4ff",
    "Kitchen Switch":           "5c3f089daa646813f26b86038b58e543",
    "Hallway Switch":           "7097e0967836d033ebde96d72e01acdf",
}
for name, did in device_ids.items():
    result = post("/api/template", {"template": f"{{{{ device_attr(\"{did}\", \"name\") }}}}"})
    print(f"  {did} -> {result.strip()}")
