---
name: home-assistant
description: Use when working on the user's Home Assistant instance — modifying scripts, automations, scenes, dashboards, helpers, or debugging entity behavior. The user's HA repo at /Users/jimjordan/Development/home-assistant holds project-organized payloads (one directory per feature) that get pushed to the live HA via REST API. Triggers on phrases like "the lights", "scene", "automation", "binary_sensor", "cover", "Hue", a wall switch, or any HA entity ID.
---

# Home Assistant — Working Notes

## Connection

- HA instance: `http://192.168.4.179:8123`
- Long-lived token: stored in `/Users/jimjordan/Development/home-assistant/get_script.py` (constant `TOKEN`)
- WebSocket URL: `ws://192.168.4.179:8123/api/websocket`

## What the local repo is

`/Users/jimjordan/Development/home-assistant` is **not** the HA config directory. It's a workspace where each feature lives in its own subdirectory with payloads + a README:

- `adaptive_lighting/` — sun/weather-driven lighting (see its README for the model)
- `garage_door/` — template cover combining two physical devices

The user does NOT have direct filesystem access to `/config/` from this machine. They edit via SSH terminal in the HA UI when needed.

## Pushing changes

### REST API (storage-backed entities — preferred path)

`script.*` and `automation.*` live in `.storage/` and have config endpoints:

```bash
TOKEN="<from get_script.py>"

# Create or update a script (object_id is the script entity name without the prefix)
curl -X POST "http://192.168.4.179:8123/api/config/script/config/<object_id>" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d @payload.json

# Create or update an automation by ID — existing automations keep their numeric ID
curl -X POST "http://192.168.4.179:8123/api/config/automation/config/<id>" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d @payload.json

# New automations: invent an ID (timestamps work well: $(date +%s))

# Delete
curl -X DELETE "http://192.168.4.179:8123/api/config/{script,automation}/config/<id>" \
     -H "Authorization: Bearer $TOKEN"
```

Payload shape: same as the YAML you'd write in the UI editor, but JSON. `triggers`/`actions`/`conditions` arrays. `mode: single|queued|parallel`.

### What CAN'T be done over REST

- **Helpers** (`input_boolean`, `input_text`, `input_number`, etc.) — require the WS admin API (`input_boolean/create`). The user must create these in the UI: Settings → Devices & Services → Helpers → Create Helper.
- **Template platforms in YAML** (template cover, template light, custom integrations) — these are config-file-only. Write the YAML, have the user SCP/nano it to `/config/packages/<name>.yaml`. Requires `homeassistant: packages: !include_dir_named packages` in `configuration.yaml`.
- **Lovelace dashboards in storage mode** — usually edited via UI; YAML mode requires file edits.

### WebSocket API (not reachable from this dev environment)

In this sandbox, `ws://...` connections fail with `OSError: [Errno 65] No route to host` even though REST works. Don't waste time retrying — fall back to REST or have the user do WS-only ops in the UI. (curl can do WS upgrades but reading the binary frames is painful.)

## Inspecting state

```bash
# All entities (large response — pipe through python json filter)
curl -sS "http://192.168.4.179:8123/api/states" -H "Authorization: Bearer $TOKEN"

# Single entity
curl -sS "http://192.168.4.179:8123/api/states/light.lounge" -H "Authorization: Bearer $TOKEN"

# Logbook
curl -sS "http://192.168.4.179:8123/api/logbook/<ISO_TIMESTAMP>" \
     -G --data-urlencode "end_time=<ISO_TIMESTAMP>" \
     -H "Authorization: Bearer $TOKEN"

# History (state changes for one entity over time)
curl -sS "http://192.168.4.179:8123/api/history/period/<ISO>?filter_entity_id=<entity>&minimal_response=true" \
     -H "Authorization: Bearer $TOKEN"
```

When parsing big responses, save to a file first — `curl … -o /tmp/states.json` — because piping to inline `python3 -c` can break on control chars.

### Reading context to identify who did something

`states/<entity>` returns `context: {id, parent_id, user_id}`. If `user_id` is set, a person triggered the change (via app/dashboard/voice). If `user_id` is null, an automation or script did it. This is invaluable for "why did this light turn on?" debugging.

## Debugging "why did entity X change"

1. Check the entity's last `context.user_id` — human or automation?
2. Look at the entity's history near the change time
3. If automation-caused, fetch its trace: Settings → Automations → pick the suspect → ⋮ → Traces
4. If a scene was applied, get its `attributes.entity_id` list to confirm the target lights
5. Search across automations: `curl /api/states | grep automation` then fetch each config: `/api/config/automation/config/<id>`

## Hue specifics

- Hue scenes spanning multiple rooms are common; the Hue Bridge sometimes flashes lights to default before settling on a scene if the lights were fully off and a transition is set. To avoid the flash, either use `transition: 0` or call `light.turn_on` with explicit values instead of `scene.turn_on`.
- Hue Color bulbs support `color_temp + xy`; Hue Ambiance bulbs (typical bathroom downlights) support `color_temp` only. To make scenes look identical across both, drive lights with `color_temp_kelvin` rather than colored Hue scenes.
- Hue's "Natural Light" reference scene values (Color Ambiance bulb): Relax 2237K/56%, Read 2890K/~80%, Concentrate 4291K/100%, Energize 6410K/~80%. White-only bulb defaults: 2700K with brightness varying (Bright 100%, Dimmed 30%, Nightlight 8% — all at 2700K).
- Hue's subtle default fade is ~0.4s; setting `transition: 0.4` matches it.

## Project conventions in this repo

- One directory per feature with a README that explains the model, payloads, and deployment
- Keep payloads as JSON files (matches REST API expectations directly)
- For automations referenced by ID, name the file after its HA ID for traceability
- Document tuning parameters (mood tables, time cutoffs) prominently in the README — these get tweaked

## When asked to "make it simpler"

The user's HA setup tends to accrete wrappers (override booleans, manual-vs-auto wrapper scripts, time-overlay logic). Before adding a new layer, ask whether an existing one can absorb the responsibility. Specifically:

- Avoid wrapper scripts when an automation can call the underlying script directly with inline pre/post steps
- Define behavior tables (like the `apply_sun_state` mood table) in **one place** — a single Jinja dict — so tuning is a one-file edit
- Prefer `light.turn_on` with explicit values over `scene.turn_on` when bulb-type consistency matters

## Latency notes

- `light.turn_on` directly: minimum latency, comparable to native Hue
- `scene.turn_on`: equivalent for Hue scenes (Hue Bridge handles)
- Adding wrapper scripts: ~100–200ms each
- The user is sensitive to wall-switch latency — keep button → action chains as flat as possible
