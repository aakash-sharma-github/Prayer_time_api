# Home Assistant example files

These files configure Home Assistant as an HTTP client of azanAPI. They do not
install a custom integration or add Home Assistant-specific code to the API.

## Install the example

1. Copy the `rest:` and `template:` sections from `configuration.yaml` into your
   Home Assistant `configuration.yaml`.
2. Replace `192.168.1.50:8000`, latitude, longitude, timezone, calculation method,
   Madhab, high-latitude rule, and all adjustment values with your own settings.
3. Copy the list in `automations.yaml` into the automations file configured by your
   Home Assistant installation. A common arrangement is
   `automation: !include automations.yaml` in `configuration.yaml`.
4. Run **Developer tools, YAML, Check configuration**. Restart Home Assistant after
   a successful check, then reload automations if you added the example automations.
5. In Developer tools, States, verify `sensor.prayer_times`, then the calculated
   entities such as `sensor.prayer_fajr` and final Azan entities such as
   `sensor.prayer_fajr_azan`.

The API must be reachable from the Home Assistant host. During local testing use a
LAN address, not `127.0.0.1`, unless Home Assistant and azanAPI run on the same host
and network namespace.

See [`docs/home-assistant.md`](../../docs/home-assistant.md) for the complete setup,
time-zone guidance, troubleshooting, and optional range-endpoint use.
