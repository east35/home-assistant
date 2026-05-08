import requests, json, re
import websocket

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def new_entity_id(eid):
    # Special case from user instructions
    if eid == "light.living_room_recessed_hue":
        return "light.living_room_downlights"
    domain, name = eid.split(".", 1)
    name = re.sub(r"_recessed", "", name)   # remove all occurrences of _recessed
    name = re.sub(r"recessed_", "", name)   # remove leading recessed_ if any
    name = re.sub(r"_+", "_", name).strip("_")  # collapse double underscores
    return f"{domain}.{name}"

# ── 1. Fetch entity registry via WebSocket ────────────────────────────────
ws = websocket.create_connection("ws://192.168.4.179:8123/api/websocket", timeout=10)
ws.recv()
ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
assert json.loads(ws.recv())["type"] == "auth_ok"

ws.send(json.dumps({"id": 1, "type": "config/entity_registry/list"}))
entity_reg = json.loads(ws.recv())["result"]

# ── 2. Find all entities with "recessed" in entity_id ────────────────────
targets = [e for e in entity_reg if "recessed" in e["entity_id"]]
targets.sort(key=lambda e: e["entity_id"])

print(f"Found {len(targets)} entities with 'recessed' in entity_id:\n")
renames = []
for e in targets:
    old_id = e["entity_id"]
    new_id = new_entity_id(old_id)
    print(f"  {old_id}  →  {new_id}")
    renames.append((old_id, new_id, e))

# ── 3. Rename each via WebSocket entity_registry/update ──────────────────
print(f"\nRenaming {len(renames)} entities...\n")
results = []
for i, (old_id, new_id, entry) in enumerate(renames, start=2):
    ws.send(json.dumps({
        "id": i,
        "type": "config/entity_registry/update",
        "entity_id": old_id,
        "new_entity_id": new_id,
    }))
    resp = json.loads(ws.recv())
    success = resp.get("success", False)
    if success:
        actual_new = resp["result"]["entity_entry"]["entity_id"]
        results.append((old_id, actual_new, True, None))
        print(f"  ✓  {old_id}  →  {actual_new}")
    else:
        error = resp.get("error", {}).get("message", str(resp))
        results.append((old_id, new_id, False, error))
        print(f"  ✗  {old_id}  →  FAILED: {error}")

ws.close()

# ── 4. Summary table ──────────────────────────────────────────────────────
print("\n\n=== Before / After ===\n")
print(f"{'Old Entity ID':<50} {'New Entity ID':<50} Status")
print("-" * 110)
for old_id, new_id, ok, err in results:
    status = "✓" if ok else f"✗ {err}"
    print(f"{old_id:<50} {new_id:<50} {status}")
