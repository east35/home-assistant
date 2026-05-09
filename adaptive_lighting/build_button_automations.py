"""Build flattened button automations for each room."""
import json, os

# room_prefix -> (automation_id, switch_ids, light_entity)
ROOMS = {
    "office_j":         ("1778266538824", ["office_switch_j_button"],                       "light.office_j"),
    "office_m":         ("1778279157280", ["office_switch_m_button"],                       "light.office_m"),
    "guest_bathroom":   ("1778279813663", ["bathroom_switch_guest_button"],                 "light.guest_bathroom"),
    "primary_bathroom": ("1778280164445", ["bathroom_switch_primary_button"],               "light.primary_bathroom"),
    "bedroom":          ("1778280182576", ["bedroom_switch_button"],                        "light.bedroom"),
    "lounge":           ("1778280198562", ["lounge_switch_1_button", "lounge_switch_2_button"], "light.lounge"),
}

ALIAS = {
    "office_j": "Office J - Scene Control",
    "office_m": "Office M - Scene Control",
    "guest_bathroom": "Guest Bathroom - Scene Control",
    "primary_bathroom": "Primary Bathroom - Scene Control",
    "bedroom": "Bedroom - Scene Control",
    "lounge": "Lounge - Scene Control",
}


def build_triggers(switches):
    triggers = []
    tid = 0
    for sw in switches:
        for sub in (1, 2, 3, 4):
            triggers.append({
                "trigger": "event",
                "event_type": "hue_event",
                "event_data": {"id": sw, "type": "short_release", "subtype": sub},
                "id": str(tid),
            })
            tid += 1
    return triggers


def on_ids(switches):
    # subtype 1 and 3 across all switches
    ids = []
    tid = 0
    for _ in switches:
        ids.append(str(tid));     tid += 1  # subtype 1
        tid += 1                              # subtype 2
        ids.append(str(tid));     tid += 1  # subtype 3
        tid += 1                              # subtype 4
    return ids


def off_ids(switches):
    ids = []
    tid = 0
    for _ in switches:
        tid += 1                              # subtype 1
        ids.append(str(tid));     tid += 1  # subtype 2
        tid += 1                              # subtype 3
        ids.append(str(tid));     tid += 1  # subtype 4
    return ids


def build(room, alias, switches, light):
    return {
        "alias": alias,
        "triggers": build_triggers(switches),
        "actions": [
            {
                "choose": [
                    {
                        "conditions": [{"condition": "trigger", "id": on_ids(switches)}],
                        "sequence": [
                            {
                                "action": "input_boolean.turn_off",
                                "target": {"entity_id": f"input_boolean.{room}_scene_override"},
                            },
                            {
                                "action": "script.apply_sun_state",
                                "data": {"room_prefix": room},
                            },
                        ],
                    },
                    {
                        "conditions": [{"condition": "trigger", "id": off_ids(switches)}],
                        "sequence": [
                            {
                                "action": "input_boolean.turn_on",
                                "target": {"entity_id": f"input_boolean.{room}_scene_override"},
                            },
                            {
                                "action": "light.turn_off",
                                "target": {"entity_id": light},
                                "data": {"transition": 0.4},
                            },
                        ],
                    },
                ]
            }
        ],
        "mode": "single",
    }


os.makedirs("payloads/automations", exist_ok=True)
for room, (aid, switches, light) in ROOMS.items():
    cfg = build(room, ALIAS[room], switches, light)
    path = f"payloads/automations/{aid}.json"
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"wrote {path}")
