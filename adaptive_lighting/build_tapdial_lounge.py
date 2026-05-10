"""Wire any Hue Tap Dial Switch to lounge actions.

Mapping (per switch):
  Button 1 → script.adaptive_lounge (always reset to adaptive; idempotent)
  Button 2 → scene.lounge_galaxy
  Button 3 → toggle LR shades (open if both closed, else close both)
  Button 4 → light.lounge off
  Rotary   → brightness_step_pct on light.lounge (steps/4)

Buttons fire on short_release. Each press is one action.

Edit SWITCHES below to add or remove devices.
"""
import json
import os
import urllib.request

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q'
HA_URL = 'http://192.168.4.179:8123'

# (hue_tap_dial_switch_<num>, friendly suffix, automation_id)
# The "switch number" is the suffix in the entity_id, not a logical index.
SWITCHES = [
    (1, "1", "1778600001000"),
    (3, "2", "1778600001003"),
]

SHORT = "{{ trigger.to_state.attributes.event_type == 'short_release' }}"

DIAL_STEP = (
    "{% set s = trigger.to_state.attributes.steps | int(1) %}"
    "{% set d = trigger.to_state.attributes.event_type %}"
    "{{ ((s / 4) | round(0)) | int if d == 'clock_wise' "
    "else ((-s / 4) | round(0)) | int }}"
)


def btn_branch(n, sequence):
    return {
        "conditions": [
            {"condition": "trigger", "id": f"btn{n}"},
            {"condition": "template", "value_template": SHORT},
        ],
        "sequence": sequence,
    }


def build_payload(switch_num, label_suffix):
    dial = f"event.hue_tap_dial_switch_{switch_num}_rotary"
    btn = f"event.hue_tap_dial_switch_{switch_num}_button_{{n}}"
    return {
        "alias": f"Hue Tap Dial {label_suffix} - Lounge",
        "description": (
            "B1 script.adaptive_lounge | B2 scene.lounge_galaxy | "
            "B3 toggle LR shades | B4 lounge off | dial brightness"
        ),
        "mode": "queued",
        "max": 10,
        "triggers": [
            {"trigger": "state", "entity_id": btn.format(n=1), "id": "btn1"},
            {"trigger": "state", "entity_id": btn.format(n=2), "id": "btn2"},
            {"trigger": "state", "entity_id": btn.format(n=3), "id": "btn3"},
            {"trigger": "state", "entity_id": btn.format(n=4), "id": "btn4"},
            {"trigger": "state", "entity_id": dial,           "id": "dial"},
        ],
        "actions": [
            {
                "choose": [
                    btn_branch(1, [
                        {"action": "script.adaptive_lounge"},
                    ]),
                    btn_branch(2, [
                        {"action": "scene.turn_on",
                         "target": {"entity_id": "scene.lounge_galaxy"}},
                    ]),
                    btn_branch(3, [
                        {
                            "choose": [{
                                "conditions": [{
                                    "condition": "template",
                                    "value_template": (
                                        "{{ states('cover.living_room_shade_1') == 'closed' "
                                        "and states('cover.living_room_shade_2') == 'closed' }}"
                                    ),
                                }],
                                "sequence": [{
                                    "action": "cover.open_cover",
                                    "target": {"entity_id": [
                                        "cover.living_room_shade_1",
                                        "cover.living_room_shade_2",
                                    ]},
                                }],
                            }],
                            "default": [{
                                "action": "cover.close_cover",
                                "target": {"entity_id": [
                                    "cover.living_room_shade_1",
                                    "cover.living_room_shade_2",
                                ]},
                            }],
                        },
                    ]),
                    btn_branch(4, [
                        {"action": "light.turn_off",
                         "target": {"entity_id": "light.lounge"},
                         "data": {"transition": 0.4}},
                    ]),
                    {
                        "conditions": [{"condition": "trigger", "id": "dial"}],
                        "sequence": [
                            {
                                "action": "light.turn_on",
                                "target": {"entity_id": "light.lounge"},
                                "data": {
                                    "brightness_step_pct": DIAL_STEP,
                                    "transition": 0.2,
                                },
                            }
                        ],
                    },
                ]
            }
        ],
    }


def push(automation_id, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{HA_URL}/api/config/automation/config/{automation_id}",
        data=body, method='POST',
        headers={'Authorization': f'Bearer {TOKEN}',
                 'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read().decode()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, 'payloads', 'automations')
    os.makedirs(out_dir, exist_ok=True)
    for switch_num, label, automation_id in SWITCHES:
        payload = build_payload(switch_num, label)
        path = os.path.join(out_dir, f'{automation_id}.json')
        with open(path, 'w') as f:
            json.dump(payload, f, indent=2)
        status, body = push(automation_id, payload)
        print(f"  ✓ Tap Dial {label} (switch_{switch_num}) → automation.{automation_id}: {status} {body}")


if __name__ == '__main__':
    main()
