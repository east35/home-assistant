import json, re
import websocket

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"

def slugify(name):
    s = name.lower()
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return re.sub(r"_+", "_", s).strip("_")

ws = websocket.create_connection("ws://192.168.4.179:8123/api/websocket", timeout=10)
ws.recv()
ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
assert json.loads(ws.recv())["type"] == "auth_ok"

ws.send(json.dumps({"id": 1, "type": "config/device_registry/list"}))
devices = json.loads(ws.recv())["result"]
ws.close()

print("All Hue switch devices:")
for d in sorted(devices, key=lambda x: x.get("name") or ""):
    name = d.get("name") or ""
    if "switch" in name.lower() and any(i[0] == "hue" for i in (d.get("identifiers") or [])):
        hue_id = slugify(name) + "_button"
        print(f"  {name!r:40} → hue_event id: {hue_id}")

print("\nLounge switch search (any device with 'lounge' in name):")
for d in devices:
    name = d.get("name") or ""
    if "lounge" in name.lower():
        hue_id = slugify(name) + "_button"
        print(f"  {name!r:40} → hue_event id: {hue_id}")
        print(f"    identifiers: {d.get('identifiers')}")
        print(f"    model      : {d.get('model')}")
        print(f"    manufacturer: {d.get('manufacturer')}")
