import requests, json
from collections import defaultdict
import websocket

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def ws_call(*messages):
    """Send multiple WS messages, return list of results in order."""
    ws = websocket.create_connection("ws://192.168.4.179:8123/api/websocket", timeout=10)
    ws.recv()  # auth_required
    ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
    auth = json.loads(ws.recv())
    assert auth["type"] == "auth_ok", f"Auth failed: {auth}"
    results = []
    for i, msg in enumerate(messages, start=1):
        msg["id"] = i
        ws.send(json.dumps(msg))
        resp = json.loads(ws.recv())
        results.append(resp.get("result", []))
    ws.close()
    return results

# Fetch entity registry and device registry in one WS session
entity_reg, device_reg = ws_call(
    {"type": "config/entity_registry/list"},
    {"type": "config/device_registry/list"},
)

# Index device registry by id
devices_by_id = {d["id"]: d for d in device_reg}

# Switch device IDs (from earlier queries)
SWITCH_DEVICE_IDS = {
    "14a947fa6612ce3fe1e1a014acac72e8": "Office Switch - J",
    "b42505161ebee80abf332ccdaea30335": "Bathroom Switch - Guest",
    "da1bbbf2a672ddc65db37642370cdc04": "Office Switch - M",
    "571ba26928a5c6382786d7d89b95c4ff": "Bathroom Switch - Primary",
    "5c3f089daa646813f26b86038b58e543": "Kitchen Switch",
    "7097e0967836d033ebde96d72e01acdf": "Hallway Switch",
    "ce41759a751836a1bb1ed9cf760df044": "Bedroom Switch",
}

print("=== Event entities for switch devices (from entity registry) ===")
for e in entity_reg:
    dev_id = e.get("device_id")
    eid = e.get("entity_id", "")
    if dev_id in SWITCH_DEVICE_IDS and eid.startswith("event."):
        print(f"\n  Device : {SWITCH_DEVICE_IDS[dev_id]}")
        print(f"  Entity : {eid}")
        print(f"  unique_id: {e.get('unique_id', '?')}")
        print(f"  name   : {e.get('name') or e.get('original_name', '?')}")
        print(f"  platform : {e.get('platform', '?')}")

# Also show ALL fields for one known entity (Office Switch J, button 3) to understand structure
print("\n\n=== Full entity registry entry for Office J button 3 ===")
for e in entity_reg:
    if e.get("entity_id") == "event.works_with_hue_switch_1_button_3":
        print(json.dumps(e, indent=2))
        break

# Show all event.* entities whose unique_id contains known hue UUIDs or slugs
print("\n=== All event.* unique_ids containing 'switch' or 'button' ===")
for e in entity_reg:
    eid = e.get("entity_id", "")
    uid = e.get("unique_id", "") or ""
    if eid.startswith("event.") and ("switch" in uid.lower() or "button" in uid.lower()):
        print(f"  {eid} -> {uid}")
