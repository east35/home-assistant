import requests

HA_URL = "http://192.168.4.179:8123"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

states = requests.get(f"{HA_URL}/api/states", headers=HEADERS).json()
lights = {
    e["entity_id"]: e["attributes"].get("friendly_name", "")
    for e in states
    if e["entity_id"].startswith("light.")
}

ROOMS = ["guest_bathroom", "hallway_garage", "kitchen_recessed", "office_m", "primary_bathroom"]

print("All light entities:")
for eid, fn in sorted(lights.items()):
    print(f"  {eid:45} | {fn}")

print("\n--- Room → light matches ---")
for room in ROOMS:
    tokens = set(room.split("_"))
    scored = []
    for eid, fn in lights.items():
        slug = eid[len("light."):]
        slug_tokens = set(slug.split("_"))
        overlap = len(tokens & slug_tokens)
        if overlap > 0:
            scored.append((overlap, eid, fn))
    scored.sort(reverse=True)
    best = scored[:3]
    print(f"\n  {room}:")
    for score, eid, fn in best:
        print(f"    [{score}] {eid} | {fn}")
