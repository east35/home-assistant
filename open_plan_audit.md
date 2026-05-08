# Open Plan Zone — Light & Scene Entity Audit

## Fixture → Entity Mapping

### Kitchen Recessed Lights

| Bulb | Entity ID | Friendly Name |
|---|---|---|
| Kitchen 1 | `light.hue_color_downlight_9` | Kitchen 1 |
| Kitchen 2 | `light.hue_color_downlight_7` | Kitchen 2 |
| Kitchen 3 | `light.hue_color_downlight_8` | Kitchen 3 |
| Kitchen 4 | `light.hue_color_downlight_6_2` | Kitchen 4 |
| Coffee nook lamp | `light.hue_color_lamp_1_4` | Coffee Nook Lamp |

**Groups:**
- `light.kitchen` ("Kitchen") — recessed 1–4 + Coffee Nook Lamp. Turning this off kills all five together. Intentional.
- `light.kitchen_group` ("Kitchen Group") — recessed 1–4 + Kitchen Pendants (no lamp)

**Scenes:** `scene.kitchen_recessed_*` (Hue room: "Kitchen")

---

### Island Pendants

| Bulb | Entity ID | Friendly Name |
|---|---|---|
| Island 1 | `light.hue_lightguide_bulb_2` | Island - 1 |
| Island 2 | `light.hue_lightguide_bulb_1` | Island - 2 |
| Island 3 | `light.hue_lightguide_bulb_3` | Island - 3 |

Grouped with the dining pendant (see below) — kept together by design.

---

### Dining Pendant

| Bulb | Entity ID | Friendly Name |
|---|---|---|
| Single pendant | `light.hue_color_lamp_1_2` | Dining Pendant |

**Group (shared with island):** `light.dining_island` ("Dining & Island") — island pendants + dining pendant controlled as one unit. Intentional.

**Scenes:** `scene.dining_island_*` (Hue room: "Dining & Island") — controls both island and dining pendant together.

---

### Living Room

| Source | Entity ID | Friendly Name |
|---|---|---|
| Downlight 1 | `light.hue_color_downlight_6` | Living Room 1 |
| Downlight 2 | `light.hue_color_downlight_5` | Living Room 2 |
| Downlight 3 | `light.hue_color_downlight_1` | Living Room 3 |
| Downlight 4 | `light.hue_color_downlight_2` | Living Room 4 |
| Downlight 5 | `light.hue_color_downlight_3` | Living Room 5 |
| Downlight 6 | `light.hue_color_downlight_4` | Living Room 6 |
| Reading lamp | `light.hue_color_lamp_2` | Large Reading Lamp |
| Accent lamp | `light.hue_ambiance_lamp_1` | Red Lamp |

**Groups:**
- `light.living_room` ("Living Room") — all 8 sources (downlights + both lamps)
- `light.living_room_downlights` ("Living Room Recessed") — 6 downlights only

**Scenes:** `scene.living_room_*` (Hue room: "Living Room")

---

### Bar Nook

| Entity ID | Friendly Name | State |
|---|---|---|
| `light.bar_nook` | Dining Room 2 ⚠ wrong name | unavailable |

Friendly name is incorrect — should be "Bar Nook". No group members. Unavailable (may be offline).

---

### Other Entities in Zone

| Entity ID | Friendly Name | Notes |
|---|---|---|
| `light.dining_overhead` | Dining Room 1 | Unavailable |
| `light.dining_room_bar_pendants` | Dining Room & Bar Pendants | Unavailable; spans two fixtures |
| `light.dining_room_pendants` | Kitchen Pendants | Entity ID says dining_room, friendly name says Kitchen — mismatch |
| `light.lounge` | Lounge | Hue **zone** (not room); 20 bulbs spanning kitchen + living room + island + hallways |
| `scene.lounge_*` | — | Zone-level scenes; control entire open plan area |
| `scene.kitchen_pendants_on/off` | — | Ungrouped, no Hue room assigned |

---

## Open Items

| Entity ID | Issue |
|---|---|
| `light.bar_nook` | Friendly name is "Dining Room 2" — needs correction |
| `light.dining_room_pendants` | Entity ID says `dining_room`, friendly name says "Kitchen Pendants" — ID mismatch |
| `light.dining_overhead` | Consistently unavailable — check if device is offline |
| `light.dining_room_bar_pendants` | Consistently unavailable — check if device is offline |
