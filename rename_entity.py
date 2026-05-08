import json
import websocket

HA_URL = "ws://192.168.4.179:8123/api/websocket"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"

ws = websocket.create_connection(HA_URL, timeout=10)
ws.recv()  # auth_required
ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
assert json.loads(ws.recv())["type"] == "auth_ok"

# Rename light.hue_color_lamp_1_4 → "Coffee Nook Lamp"
ws.send(json.dumps({
    "id": 1,
    "type": "config/entity_registry/update",
    "entity_id": "light.hue_color_lamp_1_4",
    "name": "Coffee Nook Lamp"
}))
result = json.loads(ws.recv())
ws.close()

if result.get("success"):
    entry = result["result"]["entity_entry"]
    print(f"✓ Renamed successfully")
    print(f"  entity_id : {entry['entity_id']}")
    print(f"  name      : {entry['name']}")
else:
    print(f"✗ Failed: {result}")
