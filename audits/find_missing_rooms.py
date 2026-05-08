import requests, json
import websocket

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

states = requests.get(f"{HA_URL}/api/states", headers=HEADERS).json()

scenes = {e["entity_id"]: e["attributes"] for e in states if e["entity_id"].startswith("scene.")}
lights = {e["entity_id"]: e["attributes"].get("friendly_name", "") for e in states if e["entity_id"].startswith("light.")}

# Device registry via websocket
ws = websocket.create_connection("ws://192.168.4.179:8123/api/websocket", timeout=10)
ws.recv()
ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
assert json.loads(ws.recv())["type"] == "auth_ok"
ws.send(json.dumps({"id": 1, "type": "config/device_registry/list"}))
device_reg = json.loads(ws.recv())["result"]
ws.close()

hue_switches = {
    d["id"]: d["name"]
    for d in device_reg
    if "switch" in (d.get("name") or "").lower()
    and any(i[0] == "hue" for i in (d.get("identifiers") or []))
}

import re
def slugify(name):
    s = name.lower()
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return re.sub(r"_+", "_", s).strip("_")

ROOMS = {
    "bedroom":        ["bedroom"],
    "living_room":    ["living_room"],
    "dining_island":  ["dining_island"],
    "hallway_laundry":["hallway", "hallways"],
}

REQUIRED = {"cool_bright", "relax", "rest", "nightlight"}

for room_label, prefixes in ROOMS.items():
    print(f"\n{'='*60}")
    print(f"ROOM: {room_label}")

    # Find scenes: any scene whose name starts with one of the prefixes
    # and ends with one of the 4 required suffixes
    matched_scenes = {}
    for sid in scenes:
        name = sid[len("scene."):]
        for pfx in prefixes:
            if name.startswith(pfx):
                for suffix in REQUIRED:
                    if name.endswith(f"_{suffix}"):
                        matched_scenes[suffix] = sid
    print(f"  Scenes found: {matched_scenes}")
    missing = REQUIRED - set(matched_scenes.keys())
    if missing:
        print(f"  Missing scenes: {missing}")

    # Find all scenes containing any prefix word (broader search)
    broad = [sid for sid in scenes if any(p in sid for p in prefixes)]
    print(f"  All matching scenes ({len(broad)}): {[s for s in sorted(broad)]}")

    # Find lights
    matched_lights = [(eid, fn) for eid, fn in lights.items()
                      if any(p in eid for p in prefixes)]
    print(f"  Light entities:")
    for eid, fn in sorted(matched_lights):
        print(f"    {eid} | {fn}")

    # Find switches
    matched_switches = [(did, dname) for did, dname in hue_switches.items()
                        if any(p.replace("_", " ") in dname.lower() or p in slugify(dname)
                               for p in prefixes)]
    print(f"  Switch devices:")
    for did, dname in matched_switches:
        slug = slugify(dname) + "_button"
        print(f"    {dname!r} → hue_event id: {slug}")
    if not matched_switches:
        print(f"  Switch devices: NONE FOUND")
        print(f"  All Hue switches for reference:")
        for did, dname in sorted(hue_switches.items(), key=lambda x: x[1]):
            print(f"    {dname!r} → {slugify(dname)}_button")
