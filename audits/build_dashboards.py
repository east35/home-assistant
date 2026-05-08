"""Build and push clean HA dashboards based on current entity data."""
import json, threading, websocket

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZTI5NzU3Njc1MmM0ZDk0OWRmNmJjZTMwMWYxZTUzNyIsImlhdCI6MTc3ODI1NDc4NywiZXhwIjoyMDkzNjE0Nzg3fQ.oW9kSrRxyct9dy3m0ZNx_0i3b7sbySsjTW5vYURdD4Q'

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


# ── VIEW BUILDERS ──────────────────────────────────────────────────────────────

def home_view():
    return {
        "title": "Home", "path": "home", "icon": "mdi:home",
        "cards": [
            chips(weather_chip(), person_chip("person.jim"), person_chip("person.morgan")),
            mush_climate("climate.hallway", "Thermostat"),
            mush_title("Lounge"),
            grid([
                mush_light("light.lounge", "Lounge"),
                mush_light("light.kitchen", "Kitchen"),
                mush_cover("cover.living_room_shade_1", "LR Shade 1"),
                mush_cover("cover.living_room_shade_2", "LR Shade 2"),
            ]),
            mush_title("Bedroom"),
            grid([
                mush_light("light.bedroom_recessed", "Bedroom"),
                mush_cover("cover.bedroom_shade_1", "Shade 1"),
                mush_cover("cover.master_bedroom_shade_2", "Shade 2"),
            ]),
            mush_title("Outdoors"),
            grid([
                mush_entity("cover.athom_garage_door", "Garage", "mdi:garage"),
                mush_light("light.patio", "Patio"),
                mush_light("light.outdoors", "Backyard"),
            ]),
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


def build_mobile():
    return {
        "views": [
            home_view(),
            lounge_view(),
            bedroom_view(),
            offices_view(),
            media_view(),
            outdoors_view(),
        ]
    }


def build_tablet():
    """Tablet uses wider grids (3 cols) but same structure."""
    def wide_grid(cards): return {"type": "grid", "columns": 3, "square": False, "cards": cards}

    return {
        "views": [
            {
                "title": "Home", "path": "home", "icon": "mdi:home",
                "cards": [
                    chips(weather_chip(), person_chip("person.jim"), person_chip("person.morgan")),
                    grid([
                        mush_climate("climate.hallway", "Thermostat"),
                        mush_entity("cover.athom_garage_door", "Garage", "mdi:garage"),
                    ], columns=2),
                    mush_title("Lounge"),
                    wide_grid([
                        mush_light("light.lounge", "Lounge"),
                        mush_light("light.kitchen", "Kitchen"),
                        mush_light("light.dining_island", "Dining & Island"),
                        mush_cover("cover.living_room_shade_1", "LR Shade 1"),
                        mush_cover("cover.living_room_shade_2", "LR Shade 2"),
                        mush_cover("cover.curtain_0be9", "Dining Curtain"),
                    ]),
                    mush_title("Bedroom & Bathrooms"),
                    wide_grid([
                        mush_light("light.bedroom_recessed", "Bedroom"),
                        mush_light("light.primary_bathroom", "Primary Bath"),
                        mush_light("light.guest_bathroom", "Guest Bath"),
                        mush_cover("cover.bedroom_shade_1", "Shade 1"),
                        mush_cover("cover.master_bedroom_shade_2", "Shade 2"),
                    ]),
                    mush_title("Offices"),
                    wide_grid([
                        mush_light("light.office_j", "Office J"),
                        mush_cover("cover.office_j_shade", "Office J Shade"),
                        mush_light("light.office_m_2", "Office M"),
                        mush_cover("cover.office_m_shade", "Office M Shade"),
                    ]),
                    mush_title("Media"),
                    wide_grid([
                        mush_media("media_player.apple_tv", "Apple TV"),
                        mush_media("media_player.lg_webos_tv_oled65c3pua", "LG OLED"),
                        mush_media("media_player.pioneer_vsx_lx305_60444d", "Pioneer AVR"),
                    ]),
                    mush_title("Outdoors"),
                    wide_grid([
                        mush_light("light.patio", "Patio"),
                        mush_light("light.outdoors", "Backyard"),
                    ]),
                ]
            }
        ]
    }


def build_overview():
    return {
        "views": [
            home_view(),
            lounge_view(),
            bedroom_view(),
            offices_view(),
            media_view(),
            outdoors_view(),
        ]
    }


# ── PUSH TO HA ────────────────────────────────────────────────────────────────

mobile_config  = build_mobile()
tablet_config  = build_tablet()
overview_config = build_overview()

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
            ('lovelace',           overview_config,  'overview'),
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
        print(f"{'✓' if ok else '✗'} {label}: {'saved' if ok else msg.get('error')}")
        results[rid] = ok
        if not pending:
            done.set()

def on_error(ws, err):
    print(f"WS Error: {err}")
    done.set()

ws = websocket.WebSocketApp('ws://192.168.4.179:8123/api/websocket',
                             on_message=on_message, on_error=on_error)
th = threading.Thread(target=ws.run_forever); th.daemon = True; th.start()
done.wait(timeout=20); ws.close()

print(f"\nDone. {sum(results.values())}/{len(results)} dashboards pushed.")
