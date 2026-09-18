# Home Assistant integration

## Overview

Home Assistant consumes azanAPI as a normal HTTP client. Phase 8 uses YAML only:
there is no `custom_components/` directory, Python integration, config flow, HACS
package, authentication, or Home Assistant-specific API code.

```text
Home Assistant REST/YAML -> HTTP or HTTPS -> azanAPI -> prayer-time sensors and automations
```

The single-date endpoint is the primary source for daily entities. The range endpoint
is an optional advanced API for future schedule or calendar views.

## Requirements and API availability

- A running azanAPI instance that the Home Assistant host can reach.
- Home Assistant YAML configuration access.
- Your latitude, longitude, IANA timezone, calculation method, Madhab, and
  high-latitude rule.

Verify the API from the Home Assistant host before editing YAML:

```bash
curl --get http://API_HOST:8000/api/v1/prayer-times \
  --data-urlencode latitude=25.2048 \
  --data-urlencode longitude=55.2708 \
  --data-urlencode timezone=Asia/Dubai \
  --data-urlencode calculation_method=dubai
```

Replace `API_HOST` and every example setting with your own values. If Home Assistant
runs in a container, `127.0.0.1` normally points to that container, not the host
running azanAPI. Use a LAN IP address, DNS name, or reachable container hostname.

## Basic REST configuration

Copy [configuration.yaml](../examples/home-assistant/configuration.yaml) into the
matching sections of your Home Assistant `configuration.yaml`.

The source entity, `sensor.prayer_times`, polls `GET /api/v1/prayer-times` once per
hour. It stores the date as its state and these response fields as attributes:
`calculated_times`, `azan_times`, `adjustments_minutes`, `timezone`, `coordinates`,
`calculation_method`, `madhab`, and `high_latitude_rule`. Template sensors derive
individual entities from those attributes, so Home Assistant makes one request rather
than twelve duplicate requests each polling cycle.

Change every value in the example URL:

| Setting | Example | Notes |
|---|---|---|
| API host | `192.168.1.50:8000` | Must be reachable from Home Assistant. |
| Latitude | `25.2048` | Decimal degrees from `-90` to `90`. |
| Longitude | `55.2708` | Decimal degrees from `-180` to `180`. |
| Timezone | `Asia/Dubai` | URL-encoded as `Asia%2FDubai` in the example. |
| Calculation method | `dubai` | Select the method appropriate for your location. Use `iacad_dubai` for the opt-in IACAD-validated Dubai profile. |
| Madhab | `shafi` | Use `hanafi` when appropriate. |
| High-latitude rule | `middle_of_the_night` | Change only if required. |

Supported calculation methods are `muslim_world_league`, `egyptian`, `karachi`,
`umm_al_qura`, `dubai`, `iacad_dubai`, `moon_sighting_committee`, `north_america`, `kuwait`,
`qatar`, `singapore`, and `uoif`.

`iacad_dubai` retains Dubai calculation behavior while using the IACAD-validated
internal Asr method offset. It is distinct from `asr_adjustment`, which remains a
client-specific adjustment applied only after calculated prayer times are returned.

After editing YAML, use **Developer tools, YAML, Check configuration**, restart Home
Assistant after it passes, then inspect entities in **Developer tools, States**.

## Prayer entities

The example creates seven calculated astronomical-time sensors:

| Entity | API JSON path |
|---|---|
| `sensor.prayer_fajr` | `calculated_times.fajr` |
| `sensor.prayer_sunrise` | `calculated_times.sunrise` |
| `sensor.prayer_dhuhr` | `calculated_times.dhuhr` |
| `sensor.prayer_asr` | `calculated_times.asr` |
| `sensor.prayer_sunset` | `calculated_times.sunset` |
| `sensor.prayer_maghrib` | `calculated_times.maghrib` |
| `sensor.prayer_isha` | `calculated_times.isha` |

It also creates five final Azan-time sensors:

| Entity | API JSON path |
|---|---|
| `sensor.prayer_fajr_azan` | `azan_times.fajr` |
| `sensor.prayer_dhuhr_azan` | `azan_times.dhuhr` |
| `sensor.prayer_asr_azan` | `azan_times.asr` |
| `sensor.prayer_maghrib_azan` | `azan_times.maghrib` |
| `sensor.prayer_isha_azan` | `azan_times.isha` |

Home Assistant derives IDs from names. If an existing entity causes a suffix such as
`_2`, change automation entity references to match the real IDs.

## Calculated times, Azan times, and adjustments

`calculated_times` are immutable astronomical base times. `azan_times` are final
times after the query's minute offsets. Sunrise and sunset occur only in
`calculated_times`, are not Azan prayers, and cannot be adjusted.

Use final `*_azan` sensors for call-to-prayer automations, and the calculated sensors
for astronomical display. The example includes all five adjustment parameters:

```text
fajr_adjustment=2
dhuhr_adjustment=0
asr_adjustment=0
maghrib_adjustment=0
isha_adjustment=0
```

Each accepts whole minutes from `-1440` to `1440`. Positive values move final Azan
times later and negative values move them earlier. For example, a Fajr base time of
`04:48` with `fajr_adjustment=2` produces a Fajr Azan time of `04:50`, while
`sensor.prayer_fajr` stays `04:48`.

## Timezone and updates

azanAPI returns bare local `HH:MM` values in the query's timezone. The sample
automations compare those values with Home Assistant's `now()`. Set the API timezone
and the Home Assistant instance timezone to the same local timezone. Do not request
`Asia/Dubai` while Home Assistant uses another timezone unless you add timezone-aware
conversion yourself.

The sample uses `scan_interval: 3600`. Hourly polling is sufficient for daily prayer
scheduling and refreshes the date shortly after midnight. Per-minute polling is not
needed. Large adjustments can cross midnight; a bare `HH:MM` value does not include
its rollover date, so avoid rollover-causing adjustments for time-only automations.

## Automations

Copy [automations.yaml](../examples/home-assistant/automations.yaml) into your
configured automations file. It includes Fajr and Maghrib persistent-notification
examples. They use template triggers that compare the current local minute to a final
Azan sensor, so they do not assume any particular phone, speaker, light, or media
player. Replace `persistent_notification.create` only after verifying the service and
entity available in your installation.

Because these triggers use `now()`, they evaluate once per minute. Restarting or
reloading automations during the matching minute can skip that occurrence. Treat the
examples as automations, not a guaranteed alarm system.

## Optional date range endpoint

`GET /api/v1/prayer-times/range` is useful for calendar-style dashboards, external
schedule processing, or future custom views. It accepts the same location,
calculation, and adjustment parameters as the single-date endpoint plus required,
inclusive `start_date` and `end_date`. It returns no more than 366 chronological
local dates. It is intentionally not the data source for the basic daily sensors.

## Troubleshooting

| Symptom | Likely cause and action |
|---|---|
| `sensor.prayer_times` is unavailable | Check API host, port, network route, and process. Run the curl command from the Home Assistant host. |
| HTTP `400` | Valid request that cannot be calculated. Check the IANA timezone and calculation settings. The JSON body has `error.code` and `error.message`. |
| HTTP `422` | Invalid query value. Check coordinate limits, dates, enum values, and adjustment bounds. The JSON body includes `error.details`. |
| Entities are missing | Check YAML syntax, restart Home Assistant, then check actual IDs in Developer tools. |
| Automation fires at the wrong time | Ensure Home Assistant's timezone matches the API `timezone` query parameter and use final `*_azan` sensors. |
| API works locally but not in Home Assistant | Do not use loopback addresses across hosts or containers. Use a reachable LAN/DNS address and check firewall rules. |

The API currently has no authentication, so `401` and `403` are not normal azanAPI
responses. A reverse proxy or other network layer could still produce them.

## Security considerations

For local use, Home Assistant should call azanAPI over a trusted LAN. For a public
deployment, use HTTPS through a reverse proxy in the later VPS and HTTPS phase. Do
not expose an unauthenticated development server publicly. Phase 8 adds no
authentication, API keys, Docker setup, or deployment configuration.

## References

The examples follow the official Home Assistant documentation for the
[RESTful integration](https://www.home-assistant.io/integrations/rest/),
[template integration](https://www.home-assistant.io/integrations/template/), and
[automation triggers](https://www.home-assistant.io/docs/automation/trigger/).
