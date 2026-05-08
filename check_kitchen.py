import requests

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

for eid in ["light.kitchen", "light.kitchen_group"]:
    state = requests.get(f"{HA_URL}/api/states/{eid}", headers=HEADERS).json()
    attrs = state.get("attributes", {})
    print(f"\n{eid}")
    print(f"  friendly_name : {attrs.get('friendly_name')}")
    print(f"  entity_id     : {state.get('entity_id')}")
    print(f"  supported_color_modes: {attrs.get('supported_color_modes')}")
    print(f"  entity_id list: {attrs.get('entity_id')}")  # group members if any

# Also check what entities the kitchen_recessed_cool_bright scene references
scene = requests.get(f"{HA_URL}/api/states/scene.kitchen_recessed_cool_bright", headers=HEADERS).json()
print(f"\nscene.kitchen_recessed_cool_bright attributes:")
for k, v in scene.get("attributes", {}).items():
    print(f"  {k}: {v}")
