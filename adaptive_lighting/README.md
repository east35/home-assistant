# Adaptive Lighting

A Home Assistant system that mirrors Hue's "Natural Light" dynamic scene — bulbs continuously adapt brightness and color temperature based on sun position, weather, and time of day. Custom scenes lock a room until the user toggles the wall switch.

## How it works

Pressing a wall switch ON computes a "mood" from sun elevation + weather + time of day, then calls `light.turn_on` on the room's light group with the mood's brightness and Kelvin. While lights are on, an automation re-applies the mood whenever the sun crosses an elevation threshold, weather changes, or evening time triggers fire (20:30 dim, 22:30 nightlight).

If the user picks any scene from the Hue app, Home app, dashboard, or voice assistant, that room's override flag flips ON and auto-adaptation stops until the wall switch is toggled OFF then ON.

### Mood table

| Mood          | Brightness | Kelvin | Trigger |
|---------------|-----------:|-------:|---------|
| `energize`    | 80%        | 6410K  | elev ≥ 30° AND sunny |
| `cool_bright` | 100%       | 4291K  | elev ≥ 30°, OR (elev ≥ 15° AND sunny) |
| `read`        | 80%        | 2890K  | elev ≥ 15° (overcast/heavy) |
| `relax`       | 56%        | 2237K  | elev 5°–15°, sunny/partlycloudy |
| `rest`        | 56%        | 2237K  | elev < 5°, OR heavy weather |
| `dim`         | 30%        | 2700K  | 20:30–22:30 |
| `nightlight`  | 8%         | 2700K  | ≥ 22:30 |

Values are tuned to Hue's official scene reference. Edit them in one place: `payloads/script_apply_sun_state.json` (third `variables` block).

## Components

### Scripts (HA `.storage`)
- `script.apply_sun_state` — picks mood, calls `light.turn_on` with brightness/Kelvin/transition

### Automations (HA `.storage`)
- **Auto-apply sun state to all rooms** — sun/weather/time-triggered, loops rooms, skips frozen ones (override ON) and rooms whose lights are off
- **Lock room when external scene activated** — listens to `scene.turn_on` events; if a human triggered it (`context.user_id` set) on a `scene.{room}_*`, sets that room's override
- **Lounge 6am morning** — at 06:00, clears lounge override and calls `apply_sun_state`
- **Freeze all rooms at HA startup** — sets all 6 overrides ON when HA boots
- **Per-room scene control** (×6) — wall-switch automations:
  - ON path: clear override + `apply_sun_state`
  - OFF path: set override + `light.turn_off`

### Helpers (UI-created)
6 `input_boolean.{room}_scene_override` toggles (one per room). ON = frozen, OFF = following auto.

## Rooms covered

`bedroom`, `guest_bathroom`, `lounge`, `office_j`, `office_m`, `primary_bathroom`

Each must have:
- A `light.{room_prefix}` light group
- An `input_boolean.{room_prefix}_scene_override` helper

## Files in this directory

```
adaptive_lighting/
├── README.md                                  ← this file
├── build_button_automations.py                ← regenerates the 6 button payloads
└── payloads/
    ├── script_apply_sun_state.json            ← the mood-applying script
    ├── auto_apply_sun_state.json              ← sun/weather/time auto-apply automation
    ├── detect_external_scene.json             ← locks room on Hue/dashboard scene activation
    ├── lounge_6am_v2.json                     ← 6am lounge wake-up
    └── automations/                           ← per-room button automations (filename = HA automation ID)
        ├── 1778266538824.json                 ← Office J
        ├── 1778279157280.json                 ← Office M
        ├── 1778279813663.json                 ← Guest Bathroom
        ├── 1778280164445.json                 ← Primary Bathroom
        ├── 1778280182576.json                 ← Bedroom
        └── 1778280198562.json                 ← Lounge
```

## Deploying

The HA instance is at `http://192.168.4.179:8123`. Push payloads via the REST config endpoints. Example:

```bash
TOKEN="<long-lived-token>"

# Create or update a script
curl -X POST "http://192.168.4.179:8123/api/config/script/config/apply_sun_state" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d @payloads/script_apply_sun_state.json

# Create or update an automation by ID (existing automations keep their ID)
curl -X POST "http://192.168.4.179:8123/api/config/automation/config/<id>" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d @payloads/auto_apply_sun_state.json

# Delete (e.g. obsolete scripts)
curl -X DELETE "http://192.168.4.179:8123/api/config/script/config/<id>" \
     -H "Authorization: Bearer $TOKEN"
```

Helpers (`input_boolean`) cannot be created over REST — they require the WebSocket admin API or the UI. Make them via Settings → Devices & Services → Helpers → Create Helper → Toggle.

## Tuning

To change the look:
1. Edit `payloads/script_apply_sun_state.json` — adjust the `brightness_pct` / `color_temp_kelvin` dicts
2. Push with the curl command above
3. Press a wall switch to see the new mood

To change the trigger thresholds (sun elevation, time-of-day cutoffs), edit:
- The `mood` ternary in the same file (uses `mins` for minutes-since-midnight; 1230 = 20:30, 1350 = 22:30)
- The `triggers` array in `payloads/auto_apply_sun_state.json` if you want auto-apply to fire at different times

## Verification

1. Press wall switch ON during day → instant snap to current mood, ~0.4s Hue-native fade, no flash
2. Wait for 20:30 → all on rooms transition to dim
3. Activate any `scene.lounge_*` from Hue app → `input_boolean.lounge_scene_override` flips ON within ~1s
4. Press lounge wall switch ON → override clears, mood re-applies
5. Press wall switch OFF → lights off, override locked
6. Reboot HA → all overrides ON; nothing changes lights until a button press
