import requests, json
import websocket

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Get script state/attributes
state = requests.get(f"{HA_URL}/api/states/script.apply_sun_scene", headers=HEADERS).json()
print("=== script.apply_sun_scene state ===")
print(json.dumps(state, indent=2))

# Get script config via websocket
ws = websocket.create_connection("ws://192.168.4.179:8123/api/websocket", timeout=10)
ws.recv()
ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
assert json.loads(ws.recv())["type"] == "auth_ok"

ws.send(json.dumps({"id": 1, "type": "script/config", "entity_id": "script.apply_sun_scene"}))
result = json.loads(ws.recv())
print("\n=== script config (websocket) ===")
print(json.dumps(result, indent=2))
ws.close()
