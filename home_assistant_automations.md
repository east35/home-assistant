# Home Assistant — Sun Elevation Scene Automations

All automations call `script.apply_sun_scene` with a single `room_prefix` field.
The script constructs scene entity IDs as `scene.{{ room_prefix }}_cool_bright` etc.

Switch IDs verified from live device registry on 2026-05-08.

All automations handle all 4 button subtypes:
- Subtype 1 + 3 = ON → `script.apply_sun_scene`
- Subtype 2 + 4 = OFF → `light.turn_off`

---

## Script: apply_sun_scene

```yaml
alias: Apply Sun Scene
fields:
  room_prefix:
    description: "Room prefix e.g. office_j, kitchen, guest_bathroom"
sequence:
  - choose:
      - conditions:
          - condition: numeric_state
            entity_id: sun.sun
            attribute: elevation
            above: 15
        sequence:
          - target:
              entity_id: "scene.{{ room_prefix }}_cool_bright"
            data:
              transition: 2
            action: scene.turn_on
      - conditions:
          - condition: numeric_state
            entity_id: sun.sun
            attribute: elevation
            above: 5
            below: 15
        sequence:
          - target:
              entity_id: "scene.{{ room_prefix }}_relax"
            data:
              transition: 2
            action: scene.turn_on
      - conditions:
          - condition: numeric_state
            entity_id: sun.sun
            attribute: elevation
            above: -5
            below: 5
        sequence:
          - target:
              entity_id: "scene.{{ room_prefix }}_rest"
            data:
              transition: 2
            action: scene.turn_on
      - conditions: []
        sequence:
          - target:
              entity_id: "scene.{{ room_prefix }}_nightlight"
            data:
              transition: 2
            action: scene.turn_on
mode: single
```

---

## Room Automations

### Office J — Scene Control

Switch: `office_switch_j_button`

```yaml
alias: Office J - Scene Control
triggers:
  - event_type: hue_event
    event_data:
      id: office_switch_j_button
      type: short_release
      subtype: 1
    trigger: event
    id: "0"
  - event_type: hue_event
    event_data:
      id: office_switch_j_button
      type: short_release
      subtype: 2
    trigger: event
    id: "1"
  - event_type: hue_event
    event_data:
      id: office_switch_j_button
      type: short_release
      subtype: 3
    trigger: event
    id: "2"
  - event_type: hue_event
    event_data:
      id: office_switch_j_button
      type: short_release
      subtype: 4
    trigger: event
    id: "3"
actions:
  - choose:
      - conditions:
          - condition: trigger
            id:
              - "0"
              - "2"
        sequence:
          - data:
              room_prefix: office_j
            action: script.apply_sun_scene
      - conditions:
          - condition: trigger
            id:
              - "1"
              - "3"
        sequence:
          - target:
              entity_id: light.office_j
            data:
              transition: 2
            action: light.turn_off
mode: single
```

---

### Office M — Scene Control

Switch: `office_switch_m_button`

```yaml
alias: Office M - Scene Control
triggers:
  - event_type: hue_event
    event_data:
      id: office_switch_m_button
      type: short_release
      subtype: 1
    trigger: event
    id: "0"
  - event_type: hue_event
    event_data:
      id: office_switch_m_button
      type: short_release
      subtype: 2
    trigger: event
    id: "1"
  - event_type: hue_event
    event_data:
      id: office_switch_m_button
      type: short_release
      subtype: 3
    trigger: event
    id: "2"
  - event_type: hue_event
    event_data:
      id: office_switch_m_button
      type: short_release
      subtype: 4
    trigger: event
    id: "3"
actions:
  - choose:
      - conditions:
          - condition: trigger
            id:
              - "0"
              - "2"
        sequence:
          - data:
              room_prefix: office_m
            action: script.apply_sun_scene
      - conditions:
          - condition: trigger
            id:
              - "1"
              - "3"
        sequence:
          - target:
              entity_id: light.office_m
            data:
              transition: 2
            action: light.turn_off
mode: single
```

---

### Guest Bathroom — Scene Control

Switch: `bathroom_switch_guest_button`

```yaml
alias: Guest Bathroom - Scene Control
triggers:
  - event_type: hue_event
    event_data:
      id: bathroom_switch_guest_button
      type: short_release
      subtype: 1
    trigger: event
    id: "0"
  - event_type: hue_event
    event_data:
      id: bathroom_switch_guest_button
      type: short_release
      subtype: 2
    trigger: event
    id: "1"
  - event_type: hue_event
    event_data:
      id: bathroom_switch_guest_button
      type: short_release
      subtype: 3
    trigger: event
    id: "2"
  - event_type: hue_event
    event_data:
      id: bathroom_switch_guest_button
      type: short_release
      subtype: 4
    trigger: event
    id: "3"
actions:
  - choose:
      - conditions:
          - condition: trigger
            id:
              - "0"
              - "2"
        sequence:
          - data:
              room_prefix: guest_bathroom
            action: script.apply_sun_scene
      - conditions:
          - condition: trigger
            id:
              - "1"
              - "3"
        sequence:
          - target:
              entity_id: light.guest_bathroom
            data:
              transition: 2
            action: light.turn_off
mode: single
```

---

### Primary Bathroom — Scene Control

Switch: `bathroom_switch_primary_button`

```yaml
alias: Primary Bathroom - Scene Control
triggers:
  - event_type: hue_event
    event_data:
      id: bathroom_switch_primary_button
      type: short_release
      subtype: 1
    trigger: event
    id: "0"
  - event_type: hue_event
    event_data:
      id: bathroom_switch_primary_button
      type: short_release
      subtype: 2
    trigger: event
    id: "1"
  - event_type: hue_event
    event_data:
      id: bathroom_switch_primary_button
      type: short_release
      subtype: 3
    trigger: event
    id: "2"
  - event_type: hue_event
    event_data:
      id: bathroom_switch_primary_button
      type: short_release
      subtype: 4
    trigger: event
    id: "3"
actions:
  - choose:
      - conditions:
          - condition: trigger
            id:
              - "0"
              - "2"
        sequence:
          - data:
              room_prefix: primary_bathroom
            action: script.apply_sun_scene
      - conditions:
          - condition: trigger
            id:
              - "1"
              - "3"
        sequence:
          - target:
              entity_id: light.primary_bathroom
            data:
              transition: 2
            action: light.turn_off
mode: single
```

---

### Bedroom — Scene Control

Switch: `bedroom_switch_button`

```yaml
alias: Bedroom - Scene Control
triggers:
  - event_type: hue_event
    event_data:
      id: bedroom_switch_button
      type: short_release
      subtype: 1
    trigger: event
    id: "0"
  - event_type: hue_event
    event_data:
      id: bedroom_switch_button
      type: short_release
      subtype: 2
    trigger: event
    id: "1"
  - event_type: hue_event
    event_data:
      id: bedroom_switch_button
      type: short_release
      subtype: 3
    trigger: event
    id: "2"
  - event_type: hue_event
    event_data:
      id: bedroom_switch_button
      type: short_release
      subtype: 4
    trigger: event
    id: "3"
actions:
  - choose:
      - conditions:
          - condition: trigger
            id:
              - "0"
              - "2"
        sequence:
          - data:
              room_prefix: bedroom
            action: script.apply_sun_scene
      - conditions:
          - condition: trigger
            id:
              - "1"
              - "3"
        sequence:
          - target:
              entity_id: light.bedroom
            data:
              transition: 2
            action: light.turn_off
mode: single
```

---

### Lounge — Scene Control (Open Plan)

Switch ON: `lounge_switch_1_button` or `lounge_switch_2_button` subtype 1 or 3
Switch OFF: `lounge_switch_1_button` or `lounge_switch_2_button` subtype 2 or 4
Controls: Lounge Hue zone — Living Room downlights, Kitchen, Dining & Island, Hallway (Laundry + Garage) downlights. Excludes Large Reading Lamp and Red Lamp.

```yaml
alias: Lounge - Scene Control
triggers:
  - event_type: hue_event
    event_data:
      id: lounge_switch_1_button
      type: short_release
      subtype: 1
    trigger: event
    id: "0"
  - event_type: hue_event
    event_data:
      id: lounge_switch_1_button
      type: short_release
      subtype: 2
    trigger: event
    id: "1"
  - event_type: hue_event
    event_data:
      id: lounge_switch_1_button
      type: short_release
      subtype: 3
    trigger: event
    id: "2"
  - event_type: hue_event
    event_data:
      id: lounge_switch_1_button
      type: short_release
      subtype: 4
    trigger: event
    id: "3"
  - event_type: hue_event
    event_data:
      id: lounge_switch_2_button
      type: short_release
      subtype: 1
    trigger: event
    id: "4"
  - event_type: hue_event
    event_data:
      id: lounge_switch_2_button
      type: short_release
      subtype: 2
    trigger: event
    id: "5"
  - event_type: hue_event
    event_data:
      id: lounge_switch_2_button
      type: short_release
      subtype: 3
    trigger: event
    id: "6"
  - event_type: hue_event
    event_data:
      id: lounge_switch_2_button
      type: short_release
      subtype: 4
    trigger: event
    id: "7"
actions:
  - choose:
      - conditions:
          - condition: trigger
            id:
              - "0"
              - "2"
              - "4"
              - "6"
        sequence:
          - data:
              room_prefix: lounge
            action: script.apply_sun_scene
      - conditions:
          - condition: trigger
            id:
              - "1"
              - "3"
              - "5"
              - "7"
        sequence:
          - target:
              entity_id: light.lounge
            data:
              transition: 2
            action: light.turn_off
mode: single
```

---

## Switch → Room Reference

| Switch (hue_event id) | Room | Subtypes 1+3 | Subtypes 2+4 |
|---|---|---|---|
| `office_switch_j_button` | Office J | on | off |
| `office_switch_m_button` | Office M | on | off |
| `bathroom_switch_guest_button` | Guest Bathroom | on | off |
| `bathroom_switch_primary_button` | Primary Bathroom | on | off |
| `bedroom_switch_button` | Bedroom | on | off |
| `lounge_switch_1_button` | Lounge | on | off |
| `lounge_switch_2_button` | Lounge | on | off |
