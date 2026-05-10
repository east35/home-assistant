"""Generate and push one parameterless wrapper script per room.

Creates `script.adaptive_<room>` entities — one singular action per room
that always RESETS the room to adaptive lighting:
  - clears `input_boolean.<room>_scene_override`
  - calls `script.apply_sun_state` for that room (turns lights on at the
    current mood for sun position / weather / time of day)

Idempotent — pressing it twice doesn't turn lights off. Map to Hue dimmers,
dashboard buttons, voice assistants, NFC tags, etc. without filling in a
`room_prefix` field.
"""
import json
import os
import urllib.request

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q'
HA_URL = 'http://192.168.4.179:8123'

ROOMS = {
    "lounge":           "Lounge",
    "bedroom":          "Bedroom",
    "office_j":         "Office J",
    "office_m":         "Office M",
    "guest_bathroom":   "Guest Bathroom",
    "primary_bathroom": "Primary Bathroom",
}

PAYLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'payloads')


def build_script(room_prefix, display_name):
    return {
        "alias": f"Adaptive: {display_name}",
        "icon": "mdi:lightbulb-auto",
        "description": (
            f"Singular action for {display_name}. Always resets the room to "
            "adaptive lighting: clears the override and applies the current "
            "sun-state mood. Idempotent — never turns lights off."
        ),
        "sequence": [
            {
                "action": "script.revert_room_to_auto",
                "data": {"room_prefix": room_prefix},
            }
        ],
        "mode": "queued",
        "max": 10,
    }


def push(script_id, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{HA_URL}/api/config/script/config/{script_id}",
        data=body,
        method='POST',
        headers={
            'Authorization': f'Bearer {TOKEN}',
            'Content-Type': 'application/json',
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read().decode()


def main():
    os.makedirs(PAYLOADS_DIR, exist_ok=True)
    for room, display in ROOMS.items():
        script_id = f"adaptive_{room}"
        payload = build_script(room, display)
        path = os.path.join(PAYLOADS_DIR, f"script_{script_id}.json")
        with open(path, 'w') as f:
            json.dump(payload, f, indent=2)
        try:
            status, body = push(script_id, payload)
            ok = status == 200 and 'ok' in body.lower() or status == 200
            print(f"  {'✓' if ok else '✗'} script.{script_id}: {status} {body[:80]}")
        except Exception as e:
            print(f"  ✗ script.{script_id}: {e}")


if __name__ == '__main__':
    main()
