import requests, json, re
from collections import defaultdict
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

def slugify(name):
    """Replicate HA/Hue device name slugification used in hue_event id."""
    s = name.lower()
    s = re.sub(r"[\s\-]+", "_", s)   # spaces and dashes → underscore
    s = re.sub(r"[^a-z0-9_]", "", s)  # remove anything else
    s = re.sub(r"_+", "_", s).strip("_")
    return s

states = requests.get(f"{HA_URL}/api/states", headers=HEADERS).json()
scenes_all = {e["entity_id"] for e in states if e["entity_id"].startswith("scene.")}
lights_all = {e["entity_id"]: e["attributes"].get("friendly_name","") for e in states if e["entity_id"].startswith("light.")}

# Rooms with all 4 scenes
REQUIRED = {"cool_bright", "relax", "rest", "nightlight"}
room_scenes = defaultdict(set)
for sid in scenes_all:
    name = sid[len("scene."):]
    for suffix in REQUIRED:
        if name.endswith(f"_{suffix}"):
            room_scenes[name[:-len(suffix)-1]].add(suffix)

complete_rooms = sorted(r for r, s in room_scenes.items() if REQUIRED.issubset(s))

# Pull device registry
device_reg, = ws_calls([{"type": "config/device_registry/list"}])
hue_switches = {
    d["id"]: d["name"]
    for d in device_reg
    if "switch" in (d.get("name") or "").lower()
    and any(i[0] == "hue" for i in (d.get("identifiers") or []))
}

# Derive hue_event id from device name: slugify + "_button"
# Confirmed mapping from user + live data:
#   "Office Switch - J"       → office_switch_j_button      ✓ (user confirmed, live fired)
#   "Bathroom Switch - Guest" → bathroom_switch_guest_button ✓ (user confirmed, live fired)
def hue_event_id(device_name):
    return slugify(device_name) + "_button"

print("=== Hue switch hue_event ids (derived from live device names) ===")
for dev_id, dev_name in sorted(hue_switches.items(), key=lambda x: x[1]):
    print(f"  {dev_name!r:35} → {hue_event_id(dev_name)}")

# Find best light entity for each room
def find_light(room):
    # Exact match first
    candidates = [eid for eid in lights_all if eid == f"light.{room}"]
    if candidates:
        return candidates[0]
    # Prefix match
    candidates = [eid for eid in lights_all if eid.startswith(f"light.{room}")]
    if candidates:
        return sorted(candidates)[0]
    # Fuzzy: room without trailing qualifier (e.g. kitchen_recessed → kitchen)
    base = room.rsplit("_", 1)[0]
    candidates = [eid for eid in lights_all if eid == f"light.{base}"]
    if candidates:
        return candidates[0]
    return None

# Build room → switch mapping by trying to match room name to switch name slug
def match_switch(room, switches):
    for dev_id, dev_name in switches.items():
        slug = slugify(dev_name)
        # Check if the switch slug is a prefix of the room or vice-versa
        if slug in room or room.startswith(slug.replace("_switch", "").replace("switch_", "")):
            return dev_id, dev_name
        # More specific: room contains key words from switch name
        sw_words = set(slug.split("_")) - {"switch"}
        room_words = set(room.split("_"))
        if sw_words and sw_words.issubset(room_words):
            return dev_id, dev_name
    return None, None

# Manual overrides from confirmed data
ROOM_SWITCH_OVERRIDES = {
    "guest_bathroom":   "Bathroom Switch - Guest",
    "primary_bathroom": "Bathroom Switch - Primary",
    "hallway_garage":   "Hallway Switch",
    "kitchen_recessed": "Kitchen Switch",
    "office_m":         "Office Switch - M",
    "office_j":         "Office Switch - J",   # reference, skip
}
ROOM_LIGHT_OVERRIDES = {
    "kitchen_recessed": "light.kitchen",
    "office_m":         "light.office_m_2",
}

print("\n=== Complete room summary ===")
switch_name_to_id = {v: k for k, v in hue_switches.items()}

automatable = []
no_switch = []

for room in complete_rooms:
    if room == "office_j":
        continue  # already exists

    sw_name = ROOM_SWITCH_OVERRIDES.get(room)
    light_eid = ROOM_LIGHT_OVERRIDES.get(room) or find_light(room)
    light_fn = lights_all.get(light_eid, "NOT FOUND") if light_eid else "NOT FOUND"
    light_exists = light_eid in lights_all if light_eid else False

    if sw_name:
        hue_id = hue_event_id(sw_name)
        print(f"\n  Room        : {room}")
        print(f"  Switch      : {sw_name!r} → hue_event id: {hue_id}")
        print(f"  Light       : {light_eid} ({light_fn}) {'✓' if light_exists else '✗ NOT FOUND'}")
        automatable.append((room, sw_name, hue_id, light_eid))
    else:
        print(f"\n  Room        : {room}  ← NO SWITCH FOUND")
        no_switch.append(room)

print(f"\n=== Automatable rooms ({len(automatable)}) ===")
for r, sw, hid, light in automatable:
    print(f"  {r}: switch={hid}, light={light}")

print(f"\n=== Rooms with scenes but no switch ({len(no_switch)}) ===")
for r in no_switch:
    print(f"  {r}")
