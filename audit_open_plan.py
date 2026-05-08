import requests, json

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

states = requests.get(f"{HA_URL}/api/states", headers=HEADERS).json()
by_id = {e["entity_id"]: e for e in states}

OPEN_PLAN_KEYWORDS = [
    "kitchen", "island", "dining", "living_room", "living room",
    "bar_nook", "bar nook", "pendant", "lounge"
]

def is_open_plan(eid, attrs):
    check = (eid + " " + attrs.get("friendly_name", "")).lower()
    return any(k in check for k in OPEN_PLAN_KEYWORDS)

# ── Lights ────────────────────────────────────────────────────────────────
print("=" * 70)
print("LIGHT ENTITIES — open plan zone")
print("=" * 70)

lights = {e["entity_id"]: e for e in states if e["entity_id"].startswith("light.")}
open_lights = {eid: e for eid, e in lights.items() if is_open_plan(eid, e["attributes"])}

for eid, e in sorted(open_lights.items()):
    attrs = e["attributes"]
    members = attrs.get("entity_id", [])
    fn = attrs.get("friendly_name", "")
    is_group = attrs.get("is_hue_group") or bool(members)
    print(f"\n{eid}")
    print(f"  friendly_name : {fn!r}")
    print(f"  is_hue_group  : {is_group}")
    print(f"  state         : {e['state']}")
    if members:
        print(f"  members ({len(members)}):")
        for m in members:
            mfn = lights.get(m, {}).get("attributes", {}).get("friendly_name", "?")
            print(f"    {m:45} | {mfn}")

# ── Individual bulbs not yet surfaced ─────────────────────────────────────
print("\n\n" + "=" * 70)
print("INDIVIDUAL BULBS in open-plan members (deduplicated)")
print("=" * 70)

all_members = set()
for eid, e in open_lights.items():
    for m in e["attributes"].get("entity_id", []):
        all_members.add(m)

# Also scan any light not caught by keyword filter whose friendly name suggests open plan
for eid, e in lights.items():
    fn = e["attributes"].get("friendly_name", "").lower()
    if any(k in fn for k in ["kitchen", "island", "dining", "living room", "bar nook", "pendant"]):
        all_members.add(eid)

for m in sorted(all_members):
    e = lights.get(m, by_id.get(m, {}))
    attrs = e.get("attributes", {})
    fn = attrs.get("friendly_name", "?")
    members = attrs.get("entity_id", [])
    print(f"  {m:45} | {fn}")
    if members:
        for sub in members:
            sfn = lights.get(sub, {}).get("attributes", {}).get("friendly_name", "?")
            print(f"    └─ {sub:43} | {sfn}")

# ── Scenes ────────────────────────────────────────────────────────────────
print("\n\n" + "=" * 70)
print("SCENE ENTITIES — open plan zone (grouped by Hue room)")
print("=" * 70)

from collections import defaultdict
scene_by_group = defaultdict(list)
for e in states:
    eid = e["entity_id"]
    if not eid.startswith("scene."):
        continue
    attrs = e["attributes"]
    if is_open_plan(eid, attrs):
        g = attrs.get("group_name", "ungrouped")
        scene_by_group[g].append((eid, attrs.get("name", ""), attrs.get("group_type", "?")))

for group, scenes in sorted(scene_by_group.items()):
    print(f"\n  Hue room/zone: {group!r}")
    for sid, name, gtype in sorted(scenes):
        print(f"    {sid:55} | {name!r:25} | {gtype}")
