import requests, json

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

states = requests.get(f"{HA_URL}/api/states", headers=HEADERS).json()
scenes = {e["entity_id"]: e["attributes"] for e in states if e["entity_id"].startswith("scene.")}

# Print group_name for every scene containing these room keywords
KEYWORDS = ["bedroom", "living", "dining", "island", "hallway", "hallways"]

from collections import defaultdict
by_group = defaultdict(list)
for sid, attrs in sorted(scenes.items()):
    name = sid[len("scene."):]
    if any(k in name for k in KEYWORDS):
        gname = attrs.get("group_name", "?")
        by_group[gname].append((sid, attrs.get("name", ""), attrs.get("group_type", "?")))

for group, scene_list in sorted(by_group.items()):
    print(f"\ngroup_name: {group!r}")
    for sid, name, gtype in scene_list:
        print(f"  {sid:55} | scene: {name!r:20} | type: {gtype}")

# Also: check which Hue group/room each light entity belongs to
print("\n\n--- Light entity attributes for ambiguous rooms ---")
for eid in ["light.bedroom_recessed", "light.living_room_recessed",
            "light.living_room_recessed_hue", "light.hallway_2",
            "light.hallway_garage", "light.dining_island"]:
    s = requests.get(f"{HA_URL}/api/states/{eid}", headers=HEADERS).json()
    attrs = s.get("attributes", {})
    print(f"\n{eid}")
    print(f"  friendly_name : {attrs.get('friendly_name')}")
    print(f"  entity_id list: {attrs.get('entity_id')}")
    print(f"  is_hue_group  : {attrs.get('is_hue_group')}")
    print(f"  group_name    : {attrs.get('group_name')}")
