import requests, json, re
import websocket

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

states = requests.get(f"{HA_URL}/api/states", headers=HEADERS).json()
scenes = {e["entity_id"] for e in states if e["entity_id"].startswith("scene.")}
lights = {e["entity_id"]: e["attributes"].get("friendly_name", "") for e in states if e["entity_id"].startswith("light.")}

REQUIRED = ["cool_bright", "relax", "rest", "nightlight"]

def check_prefix(prefix):
    results = {}
    for suffix in REQUIRED:
        eid = f"scene.{prefix}_{suffix}"
        results[suffix] = eid if eid in scenes else "MISSING"
    return results

# Candidate prefixes to verify
CANDIDATES = {
    "guest_bathroom":   "guest_bathroom",
    "hallway_garage":   "hallway_garage",
    "kitchen":          "kitchen_recessed",
    "office_m":         "office_m",
    "primary_bathroom": "primary_bathroom",
    "bedroom":          "bedroom_recessed",
    "lounge":           "lounge",
    "office_j":         "office_j",
}

print("=== Scene prefix verification ===")
for label, prefix in CANDIDATES.items():
    result = check_prefix(prefix)
    ok = all(v != "MISSING" for v in result.values())
    print(f"\n  {label} (prefix: {prefix!r}) {'✓' if ok else '✗'}")
    for suffix, eid in result.items():
        print(f"    {suffix:15} → {eid}")

# Bedroom: also check if 'bedroom' (not 'bedroom_recessed') works for non-cool_bright scenes
print("\n=== Bedroom scene names — exact check ===")
bedroom_scenes = sorted(s for s in scenes if s.startswith("scene.bedroom"))
for s in bedroom_scenes:
    print(f"  {s}")

# Verify light entities for lounge automation
print("\n=== Light entity verification for Lounge automation ===")
for eid in ["light.living_room", "light.living_room_recessed",
            "light.kitchen", "light.dining_island"]:
    exists = eid in lights
    fn = lights.get(eid, "NOT FOUND")
    print(f"  {eid:40} {'✓' if exists else '✗ NOT FOUND':20} | {fn}")

# Verify hue_event IDs from device registry
print("\n=== Hue switch device registry ===")
ws = websocket.create_connection("ws://192.168.4.179:8123/api/websocket", timeout=10)
ws.recv()
ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
assert json.loads(ws.recv())["type"] == "auth_ok"
ws.send(json.dumps({"id": 1, "type": "config/device_registry/list"}))
devices = json.loads(ws.recv())["result"]
ws.close()

def slugify(name):
    s = name.lower()
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return re.sub(r"_+", "_", s).strip("_")

for d in sorted(devices, key=lambda x: x.get("name") or ""):
    name = d.get("name") or ""
    if "switch" in name.lower() and any(i[0] == "hue" for i in (d.get("identifiers") or [])):
        print(f"  {name!r:40} → {slugify(name)}_button")
