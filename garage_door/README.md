# Garage Door

A unified `cover.garage` entity built from two physical devices that together form one logical garage door:

- **`cover.athom_garage_door`** — ESP-based controller; can open/close but no longer reports position reliably
- **`binary_sensor.garage`** — secondary positional sensor added to compensate

The template cover combines them: state from the sensor, control commands forwarded to the athom.

## How it works

`cover.garage` is a [Template Cover](https://www.home-assistant.io/integrations/cover.template/):
- `value_template` reads `binary_sensor.garage` (`on` = open)
- `open_cover` / `close_cover` / `stop_cover` delegate to `cover.athom_garage_door`

Because it's a real entity, it's available to automations, HomeKit, voice assistants, and any dashboard card — unlike a Lovelace-only solution.

## Automations

Currently bundled:
- **Notify if garage open after sunset** — fires if `cover.garage` has been `open` for 5+ minutes after sunset, sends a notification

Add more automations to `garage_door.yaml` under the same `automation:` block.

## Files

```
garage_door/
├── README.md
└── garage_door.yaml   ← template cover + automations (HA package format)
```

## Deploying

Unlike the adaptive_lighting project (which uses HA's REST config API to write to `.storage/`), the template cover platform is YAML-only. It must live as a file on the HA host.

This file is intended to be installed as an HA **package** at `/config/packages/garage_door.yaml`.

### One-time setup

In `configuration.yaml`, ensure the packages directory is loaded:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

### Install / update

SSH into the HA host (e.g. via the official SSH add-on terminal) and:

```bash
mkdir -p /config/packages
nano /config/packages/garage_door.yaml
# paste the contents of garage_door.yaml from this repo, save (Ctrl+O Enter, Ctrl+X)
```

Then in the HA UI: Developer Tools → YAML → **Check Configuration** → if green, **Restart**.

After restart, `cover.garage` appears in Developer Tools → States.

## Tuning

- If `binary_sensor.garage` reports inverted (on = closed), flip the `value_template` to `is_state(..., 'off')`
- The notify automation calls `notify.notify` — replace with your specific mobile-app service (e.g. `notify.mobile_app_iphone`) for a guaranteed-delivery target

## HomeKit / voice cleanup

After `cover.garage` works, hide the original `cover.athom_garage_door` and `binary_sensor.garage` from HomeKit Bridge / Google / Alexa so they don't appear as duplicates. Hide via Settings → Devices & Services → HomeKit Bridge → Configure (and Voice Assistants for Google/Alexa).
