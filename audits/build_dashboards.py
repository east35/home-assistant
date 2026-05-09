"""Build and push clean HA dashboards based on current entity data.

Soft-UI styled layout: header (clock + weather), person/lights chips,
Lights/Climate quick actions, and a Rooms grid sourced live from the area
+ entity registries. Snapshots existing dashboards before pushing so a
broken result can be reverted with `dashboards_restore.py`.
"""
import json
import os
import sys
import threading
from collections import defaultdict

import websocket  # type: ignore

# Local snapshot helper (in same dir).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dashboards_backup import backup_dashboards  # noqa: E402

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q'
WS_URL = 'ws://192.168.4.179:8123/api/websocket'

def mush_title(title, subtitle=None):
    c = {"type": "custom:mushroom-title-card", "title": title}
    if subtitle: c["subtitle"] = subtitle
    return c

def mush_light(entity, name=None, show_brightness=True):
    c = {"type": "custom:mushroom-light-card", "entity": entity,
         "show_brightness_control": show_brightness,
         "show_color_temp_control": True, "show_color_control": False,
         "use_light_color": True, "fill_container": True}
    if name: c["name"] = name
    return c

def mush_cover(entity, name=None):
    c = {"type": "custom:mushroom-cover-card", "entity": entity,
         "show_buttons_control": True, "show_position_control": True,
         "fill_container": True}
    if name: c["name"] = name
    return c

def mush_entity(entity, name=None, icon=None):
    c = {"type": "custom:mushroom-entity-card", "entity": entity,
         "fill_container": True}
    if name: c["name"] = name
    if icon: c["icon"] = icon
    return c

def mush_media(entity, name=None):
    c = {"type": "media-control", "entity": entity}
    return c

def mush_climate(entity, name=None):
    c = {"type": "thermostat", "entity": entity}
    return c

def grid(cards, columns=2, square=False):
    return {"type": "grid", "columns": columns, "square": square, "cards": cards}

def chips(*chip_list):
    return {"type": "custom:mushroom-chips-card", "chips": list(chip_list),
            "alignment": "center"}

def person_chip(entity):
    return {"type": "person", "entity": entity}

def weather_chip(entity="weather.forecast_lullwood"):
    return {"type": "weather", "entity": entity, "show_conditions": True, "show_temperature": True}

def entity_chip(entity, icon=None):
    c = {"type": "entity", "entity": entity}
    if icon: c["icon"] = icon
    return c

def section(title, cards, columns=2):
    return [mush_title(title)] + [grid(cards, columns=columns, square=False)]


# ── ENTITY DISCOVERY ───────────────────────────────────────────────────────────

def _ws_request(payloads):
    """Open one WebSocket, run a list of (label, payload) requests, return
    {label: result}. Auth handled inside."""
    out = {}
    pending = {}
    msg_id = [1]
    done = threading.Event()

    def on_message(ws, message):
        msg = json.loads(message)
        t = msg.get('type')
        if t == 'auth_required':
            ws.send(json.dumps({'type': 'auth', 'access_token': TOKEN}))
        elif t == 'auth_ok':
            for label, payload in payloads:
                cid = msg_id[0]; msg_id[0] += 1
                pending[cid] = label
                ws.send(json.dumps({**payload, 'id': cid}))
        elif t == 'result':
            label = pending.pop(msg['id'])
            out[label] = msg.get('result')
            if not pending:
                done.set()

    def on_error(ws, err):
        print(f"WS Error: {err}")
        done.set()

    ws = websocket.WebSocketApp(WS_URL, on_message=on_message, on_error=on_error)
    th = threading.Thread(target=ws.run_forever); th.daemon = True; th.start()
    done.wait(timeout=20); ws.close()
    return out


# Temperature sensors we never want to surface as room temperature.
TEMP_BLACKLIST = ('drive', 'disk', 'stargazer', 'cpu', 'gpu', 'battery',
                  'hub_2_', '_internal', '_outdoor')


def fetch_topology():
    """Probe HA registries + states; return {area_id: {category: [entities]}}."""
    res = _ws_request([
        ('areas',    {'type': 'config/area_registry/list'}),
        ('entities', {'type': 'config/entity_registry/list'}),
        ('devices',  {'type': 'config/device_registry/list'}),
        ('states',   {'type': 'get_states'}),
    ])
    states = {s['entity_id']: s for s in res['states']}
    device_to_area = {d['id']: d.get('area_id') for d in res['devices']}

    ent_area = {}
    for e in res['entities']:
        aid = e.get('area_id') or device_to_area.get(e.get('device_id'))
        if aid:
            ent_area[e['entity_id']] = aid

    buckets = defaultdict(lambda: defaultdict(list))
    for eid, aid in ent_area.items():
        domain = eid.split('.')[0]
        attrs = (states.get(eid, {}) or {}).get('attributes', {}) or {}
        dc = attrs.get('device_class')
        if domain == 'sensor' and dc == 'temperature':
            buckets[aid]['temperature'].append(eid)
        elif domain == 'binary_sensor' and dc in ('window', 'door', 'opening'):
            buckets[aid]['window'].append(eid)
        elif domain == 'binary_sensor' and dc in ('motion', 'occupancy', 'presence'):
            buckets[aid]['motion'].append(eid)
        elif domain == 'binary_sensor' and dc == 'smoke':
            buckets[aid]['smoke'].append(eid)
        elif domain == 'media_player':
            buckets[aid]['media'].append(eid)
        elif domain == 'climate':
            buckets[aid]['climate'].append(eid)
    return {aid: dict(cats) for aid, cats in buckets.items()}


def _pick_temp(entities):
    for e in entities or []:
        if not any(b in e for b in TEMP_BLACKLIST):
            return e
    return None


# ── SOFT-UI CARD FACTORIES ─────────────────────────────────────────────────────

def clock_card():
    return {
        "type": "custom:mushroom-template-card",
        "primary": "{{ now().strftime('%A, %-d %B') }}",
        "secondary": "{{ now().strftime('%H:%M') }}",
        "icon": "mdi:calendar-clock",
        "icon_color": "blue",
        "fill_container": True,
    }


def weather_card(weather_entity="weather.forecast_lullwood"):
    return {
        "type": "custom:mushroom-template-card",
        "primary": "{{ state_attr('" + weather_entity + "','temperature') }}°",
        "secondary": "{{ states('" + weather_entity + "') | replace('_',' ') | title }}",
        "icon": "mdi:weather-{{ states('" + weather_entity + "') | replace('-','-') }}",
        "icon_color": "amber",
        "fill_container": True,
        "tap_action": {"action": "more-info", "entity": weather_entity},
    }


def header_row():
    return grid([clock_card(), weather_card()], columns=2)


def lights_on_chip():
    return {
        "type": "template",
        "icon": "mdi:lightbulb",
        "icon_color": "amber",
        "content": "{{ states.light | selectattr('state','eq','on') | list | count }} on",
        "tap_action": {"action": "navigate", "navigation_path": "/dashboard-mushroom/lights"},
    }


def quick_action(label, icon, color, nav_path):
    return {
        "type": "custom:mushroom-template-card",
        "primary": label,
        "icon": icon,
        "icon_color": color,
        "fill_container": True,
        "tap_action": {"action": "navigate", "navigation_path": nav_path},
    }


def room_card(name, icon, nav_path, sensors):
    """sensors = dict from fetch_topology()[area_id]; missing keys hidden."""
    parts = []
    temp = _pick_temp(sensors.get('temperature'))
    if temp:
        parts.append(
            "{% set t = states('" + temp + "') %}"
            "{% if t not in ['unknown','unavailable'] %}{{ t }}°{% endif %}"
        )

    def any_state(eids, target):
        return " or ".join(f"is_state('{e}','{target}')" for e in eids)

    if sensors.get('window'):
        parts.append("{% if " + any_state(sensors['window'], 'on') + " %} 🪟{% endif %}")
    if sensors.get('motion'):
        parts.append("{% if " + any_state(sensors['motion'], 'on') + " %} 🚶{% endif %}")
    if sensors.get('media'):
        parts.append("{% if " + any_state(sensors['media'], 'playing') + " %} 🔊{% endif %}")
    if sensors.get('smoke'):
        parts.append("{% if " + any_state(sensors['smoke'], 'on') + " %} 🔥{% endif %}")

    secondary = "".join(parts) if parts else " "
    return {
        "type": "custom:mushroom-template-card",
        "primary": name,
        "secondary": secondary,
        "icon": icon,
        "icon_color": "blue",
        "fill_container": True,
        "tap_action": {"action": "navigate", "navigation_path": nav_path},
    }


# (display_name, area_id, mdi icon, navigation path for tap)
ROOMS = [
    ("Living Room",     "living_room",      "mdi:sofa",                     "/dashboard-mushroom/lounge"),
    ("Kitchen",         "kitchen",          "mdi:countertop",               "/dashboard-mushroom/lounge"),
    ("Dining & Island", "dining_island",    "mdi:silverware-fork-knife",    "/dashboard-mushroom/lounge"),
    ("Bedroom",         "bedroom",          "mdi:bed",                      "/dashboard-mushroom/bedroom"),
    ("Primary Bath",    "primary_bathroom", "mdi:shower",                   "/dashboard-mushroom/bedroom"),
    ("Guest Bath",      "guest_bathroom",   "mdi:toilet",                   "/dashboard-mushroom/bedroom"),
    ("Office - J",      "office_j",         "mdi:desk",                     "/dashboard-mushroom/offices"),
    ("Office - M",      "office_m",         "mdi:desk",                     "/dashboard-mushroom/offices"),
    ("Hall - Garage",   "hallway_garage",   "mdi:door",                     "/dashboard-mushroom/lounge"),
    ("Hall - Laundry",  "hallway_laundry",  "mdi:washing-machine",          "/dashboard-mushroom/lounge"),
    ("Patio",           "patio",            "mdi:umbrella-beach",           "/dashboard-mushroom/outdoors"),
    ("Backyard",        "backyard",         "mdi:tree",                     "/dashboard-mushroom/outdoors"),
]


def rooms_grid(topology, columns=2):
    cards = [
        room_card(name, icon, nav, topology.get(area_id, {}))
        for (name, area_id, icon, nav) in ROOMS
    ]
    return grid(cards, columns=columns)


# ── HOME-VIEW WIDGETS (per docs/dashboard.md) ──────────────────────────────────

SHADES = [
    ("LR Shade 1",   "cover.living_room_shade_1"),
    ("LR Shade 2",   "cover.living_room_shade_2"),
    ("Bed Shade 1",  "cover.bedroom_shade_1"),
    ("Bed Shade 2",  "cover.master_bedroom_shade_2"),
    ("Office J",     "cover.office_j_shade"),
    ("Office M",     "cover.office_m_shade"),
    ("Dining Curt.", "cover.curtain_0be9"),
]

WINDOW_SENSORS = [
    ("Living Rm 1",  "binary_sensor.window_l_1"),
    ("Living Rm 2",  "binary_sensor.window_l_2"),
    ("Bedroom F",    "binary_sensor.window_mb_front"),
    ("Bedroom S",    "binary_sensor.window_mb_side"),
    ("Office J",     "binary_sensor.window_j"),
    ("Office M",     "binary_sensor.window_m"),
]

ROOM_LIGHTS = [
    ("Living Room",     "light.living_room"),
    ("Kitchen",         "light.kitchen"),
    ("Dining & Island", "light.dining_island"),
    ("Bedroom",         "light.bedroom"),
    ("Primary Bath",    "light.primary_bathroom"),
    ("Guest Bath",      "light.guest_bathroom"),
    ("Office - J",      "light.office_j"),
    ("Office - M",      "light.office_m"),
    ("Hall - Garage",   "light.hallway_garage"),
    ("Hall - Laundry",  "light.hallway_2"),
    ("Patio",           "light.patio"),
    ("Backyard",        "light.outdoors"),
]

MEDIA_PLAYERS = [
    "media_player.apple_tv",
    "media_player.lg_webos_tv_oled65c3pua",
    "media_player.pioneer_vsx_lx305_60444d",
]


def shades_section(columns=2):
    return [mush_title("Shades"),
            grid([mush_cover(eid, name) for name, eid in SHADES], columns=columns)]


def garage_card():
    return {
        "type": "custom:mushroom-cover-card",
        "entity": "cover.athom_garage_door",
        "name": "Garage Door",
        "icon": "mdi:garage",
        "show_buttons_control": True,
        "fill_container": True,
    }


def window_sensors_chips():
    """One chip per window sensor; red when open, neutral when closed."""
    chip_list = []
    for name, eid in WINDOW_SENSORS:
        chip_list.append({
            "type": "template",
            "entity": eid,
            "icon": "{% if is_state('" + eid + "','on') %}mdi:window-open-variant{% else %}mdi:window-closed-variant{% endif %}",
            "icon_color": "{% if is_state('" + eid + "','on') %}red{% else %}grey{% endif %}",
            "content": name,
            "tap_action": {"action": "more-info"},
        })
    return {
        "type": "custom:mushroom-chips-card",
        "alignment": "start",
        "chips": chip_list,
    }


def room_lighting_grid(columns=2):
    return grid([mush_light(eid, name) for name, eid in ROOM_LIGHTS], columns=columns)


def synology_card():
    return {
        "type": "entities",
        "title": "Ceres (Synology NAS)",
        "show_header_toggle": False,
        "entities": [
            {"entity": "sensor.stargazer_volume_1_volume_used",
             "name": "Volume Used",       "icon": "mdi:harddisk"},
            {"entity": "sensor.stargazer_volume_1_status",
             "name": "Volume Status",     "icon": "mdi:check-circle"},
            {"entity": "sensor.stargazer_cpu_utilization_total",
             "name": "CPU",               "icon": "mdi:cpu-64-bit"},
            {"entity": "sensor.stargazer_memory_usage_real",
             "name": "Memory",            "icon": "mdi:memory"},
            {"entity": "sensor.stargazer_temperature",
             "name": "System Temp",       "icon": "mdi:thermometer"},
            {"entity": "sensor.stargazer_download_throughput",
             "name": "Download",          "icon": "mdi:download"},
            {"entity": "sensor.stargazer_upload_throughput",
             "name": "Upload",            "icon": "mdi:upload"},
            {"entity": "update.stargazer_dsm_update",
             "name": "DSM Update"},
            {"entity": "binary_sensor.stargazer_security_status",
             "name": "Security"},
        ],
    }


def now_playing_card():
    """Stack of conditional media-control cards — only visible when playing."""
    return {
        "type": "vertical-stack",
        "cards": [
            {
                "type": "conditional",
                "conditions": [{"entity": eid, "state_not": "off"},
                               {"entity": eid, "state_not": "unavailable"},
                               {"entity": eid, "state_not": "idle"},
                               {"entity": eid, "state_not": "standby"}],
                "card": {"type": "media-control", "entity": eid},
            }
            for eid in MEDIA_PLAYERS
        ],
    }


# ── VIEW BUILDERS ──────────────────────────────────────────────────────────────

def home_view(topology, *, rooms_columns=2):
    return {
        "title": "Home", "path": "home", "icon": "mdi:home",
        "cards": [
            header_row(),
            chips(person_chip("person.jim"), person_chip("person.morgan"), lights_on_chip()),
            grid([
                quick_action("Lights",  "mdi:lamps",       "amber", "/dashboard-mushroom/lights"),
                quick_action("Climate", "mdi:thermometer", "blue",  "/dashboard-mushroom/climate"),
            ], columns=2),

            mush_title("Now Playing"),
            now_playing_card(),

            mush_title("Climate"),
            mush_climate("climate.hallway", "Thermostat"),

            mush_title("Garage"),
            garage_card(),

            mush_title("Shades"),
            grid([mush_cover(eid, name) for name, eid in SHADES], columns=rooms_columns),

            mush_title("Windows"),
            window_sensors_chips(),

            mush_title("Room Lighting"),
            room_lighting_grid(columns=rooms_columns),

            mush_title("Synology"),
            synology_card(),

            mush_title("Rooms"),
            rooms_grid(topology, columns=rooms_columns),
        ]
    }


def lights_view():
    return {
        "title": "Lights", "path": "lights", "icon": "mdi:lamps",
        "cards": [
            mush_title("All Lights"),
            grid([
                mush_light("light.living_room", "Living Room"),
                mush_light("light.kitchen", "Kitchen"),
                mush_light("light.dining_island", "Dining & Island"),
                mush_light("light.bedroom", "Bedroom"),
                mush_light("light.primary_bathroom", "Primary Bath"),
                mush_light("light.guest_bathroom", "Guest Bath"),
                mush_light("light.office_j", "Office - J"),
                mush_light("light.office_m", "Office - M"),
                mush_light("light.hallway_garage", "Hall - Garage"),
                mush_light("light.hallway_2", "Hall - Laundry"),
                mush_light("light.patio", "Patio"),
                mush_light("light.outdoors", "Backyard"),
            ], columns=2),
        ]
    }


def climate_view():
    return {
        "title": "Climate", "path": "climate", "icon": "mdi:thermometer",
        "cards": [
            mush_climate("climate.hallway", "Thermostat"),
        ]
    }


def lounge_view():
    return {
        "title": "Lounge", "path": "lounge", "icon": "mdi:sofa",
        "cards": [
            mush_title("Living Room"),
            grid([
                mush_light("light.living_room_recessed", "Recessed"),
                mush_light("light.hue_color_lamp_2", "Floor Lamp"),
                mush_light("light.hue_play_1", "Hue Play 1"),
                mush_light("light.hue_play_2", "Hue Play 2"),
                mush_light("light.record_shelf", "Record Shelf"),
                mush_cover("cover.living_room_shade_1", "Shade 1"),
                mush_cover("cover.living_room_shade_2", "Shade 2"),
            ]),
            mush_title("Kitchen"),
            grid([
                mush_light("light.kitchen", "Recessed"),
                mush_light("light.hue_color_lamp_1_2", "Pendant 1"),
                mush_light("light.hue_color_lamp_1_4", "Pendant 2"),
                mush_entity("switch.bar_nook", "Bar Nook", "mdi:wall-sconce"),
                mush_entity("switch.hue_outlet", "Hue Outlet", "mdi:power-socket"),
            ]),
            mush_title("Dining & Island"),
            grid([
                mush_light("light.dining_island", "Dining & Island"),
                mush_light("light.hue_lightguide_bulb_1", "Island 1"),
                mush_light("light.hue_lightguide_bulb_2", "Island 2"),
                mush_light("light.hue_lightguide_bulb_3", "Island 3"),
                mush_cover("cover.curtain_0be9", "Curtain"),
            ]),
            mush_title("Hallways"),
            grid([
                mush_light("light.hallway_garage", "Hallway - Garage"),
                mush_light("light.hallway_2", "Hallway - Laundry"),
            ]),
        ]
    }


def bedroom_view():
    return {
        "title": "Bedroom", "path": "bedroom", "icon": "mdi:bed",
        "cards": [
            mush_title("Bedroom"),
            grid([
                mush_light("light.bedroom_recessed", "Recessed"),
                mush_cover("cover.bedroom_shade_1", "Shade 1"),
                mush_cover("cover.master_bedroom_shade_2", "Shade 2"),
            ]),
            mush_title("Primary Bathroom"),
            grid([
                mush_light("light.primary_bathroom", "Primary Bath"),
            ]),
            mush_title("Guest Bathroom"),
            grid([
                mush_light("light.guest_bathroom", "Guest Bath"),
            ]),
        ]
    }


def offices_view():
    return {
        "title": "Offices", "path": "offices", "icon": "mdi:desk",
        "cards": [
            mush_title("Office – J"),
            grid([
                mush_light("light.office_j", "Recessed"),
                mush_light("light.hue_play_1_2", "Hue Play"),
                mush_light("light.hue_signe_table_1", "Signe Table"),
                mush_cover("cover.office_j_shade", "Shade"),
            ]),
            mush_title("Office – M"),
            grid([
                mush_light("light.office_m_2", "Recessed"),
                mush_cover("cover.office_m_shade", "Shade"),
            ]),
        ]
    }


def media_view():
    return {
        "title": "Media", "path": "media", "icon": "mdi:television-play",
        "cards": [
            mush_title("Living Room"),
            mush_media("media_player.apple_tv", "Apple TV"),
            mush_media("media_player.lg_webos_tv_oled65c3pua", "LG OLED"),
            mush_media("media_player.pioneer_vsx_lx305_60444d", "Pioneer AVR"),
            mush_title("Scenes"),
            grid([
                mush_entity("scene.lounge_movie_night", "Movie Night", "mdi:movie"),
                mush_entity("scene.lounge_natural_light", "Natural Light", "mdi:weather-sunny"),
                mush_entity("scene.lounge_relax", "Relax", "mdi:candle"),
                mush_entity("scene.lounge_bright", "Bright", "mdi:lightbulb-on"),
                mush_entity("scene.tv_time", "TV Time", "mdi:television"),
                mush_entity("scene.diablo_4_on", "Diablo 4", "mdi:gamepad-variant"),
            ]),
        ]
    }


def outdoors_view():
    return {
        "title": "Outdoors", "path": "outdoors", "icon": "mdi:tree",
        "cards": [
            mush_title("Patio"),
            grid([
                mush_light("light.patio", "Patio"),
                mush_light("light.hue_lily_outdoor_spotlight_2", "Spotlight 2"),
                mush_light("light.hue_lily_outdoor_spotlight_3", "Spotlight 3"),
                mush_light("light.hue_lily_outdoor_spotlight_4", "Spotlight 4"),
                mush_light("light.hue_lily_outdoor_spotlight_5", "Spotlight 5"),
            ]),
            mush_title("Backyard"),
            grid([
                mush_entity("cover.athom_garage_door", "Garage Door", "mdi:garage"),
                mush_light("light.outdoors", "Backyard Lights"),
            ]),
            mush_title("Irrigation"),
            grid([
                mush_entity("switch.lawn_schedule", "Lawn", "mdi:sprinkler"),
                mush_entity("switch.garden_schedule", "Garden", "mdi:flower"),
                mush_entity("switch.seeding_schedule", "Seeding", "mdi:seed"),
                mush_entity("switch.shady_front_yard", "Shady Front", "mdi:sprinkler"),
                mush_entity("switch.sunny_front_corner", "Sunny Front", "mdi:sprinkler"),
                mush_entity("switch.front_slope_bed", "Slope Bed", "mdi:sprinkler"),
            ]),
        ]
    }


def build_mobile(topology):
    return {
        "views": [
            home_view(topology, rooms_columns=2),
            lights_view(),
            climate_view(),
            lounge_view(),
            bedroom_view(),
            offices_view(),
            media_view(),
            outdoors_view(),
        ]
    }


def build_tablet(topology):
    return {
        "views": [
            home_view(topology, rooms_columns=3),
            lights_view(),
            climate_view(),
            lounge_view(),
            bedroom_view(),
            offices_view(),
            media_view(),
            outdoors_view(),
        ]
    }


def build_overview(topology):
    return {
        "views": [
            home_view(topology, rooms_columns=3),
            lights_view(),
            climate_view(),
            lounge_view(),
            bedroom_view(),
            offices_view(),
            media_view(),
            outdoors_view(),
        ]
    }


# ── PUSH TO HA ────────────────────────────────────────────────────────────────

print("Step 1/3: snapshotting current dashboards…")
backup_dir = backup_dashboards()
print(f"\n  Restore with: python3 audits/dashboards_restore.py {backup_dir}\n")

print("Step 2/3: discovering entity topology…")
topology = fetch_topology()
print(f"  Found sensors in {len(topology)} areas.\n")

print("Step 3/3: building and pushing new dashboards…")
mobile_config   = build_mobile(topology)
tablet_config   = build_tablet(topology)
overview_config = build_overview(topology)

with open('/tmp/new_mobile_dashboard.json', 'w') as f:
    json.dump(mobile_config, f, indent=2)
with open('/tmp/new_tablet_dashboard.json', 'w') as f:
    json.dump(tablet_config, f, indent=2)
with open('/tmp/new_overview_dashboard.json', 'w') as f:
    json.dump(overview_config, f, indent=2)

results = {}
done = threading.Event()
msg_id = [1]
pending = {}

def on_message(ws, message):
    msg = json.loads(message)
    t = msg.get('type')
    if t == 'auth_required':
        ws.send(json.dumps({'type': 'auth', 'access_token': TOKEN}))
    elif t == 'auth_ok':
        for url_path, config, label in [
            ('dashboard-mushroom', mobile_config,  'mobile'),
            ('dashboard-tablet',   tablet_config,   'tablet'),
            ('lovelace',           overview_config, 'overview'),
        ]:
            cid = msg_id[0]; msg_id[0] += 1
            pending[cid] = label
            ws.send(json.dumps({
                'id': cid,
                'type': 'lovelace/config/save',
                'url_path': url_path,
                'config': config,
            }))
    elif t == 'result':
        rid = msg['id']
        label = pending.pop(rid, '?')
        ok = msg.get('success')
        print(f"  {'✓' if ok else '✗'} {label}: {'saved' if ok else msg.get('error')}")
        results[rid] = ok
        if not pending:
            done.set()

def on_error(ws, err):
    print(f"WS Error: {err}")
    done.set()

ws = websocket.WebSocketApp(WS_URL, on_message=on_message, on_error=on_error)
th = threading.Thread(target=ws.run_forever); th.daemon = True; th.start()
done.wait(timeout=20); ws.close()

print(f"\nDone. {sum(results.values())}/{len(results)} dashboards pushed.")
print(f"Rollback: python3 audits/dashboards_restore.py {backup_dir}")
