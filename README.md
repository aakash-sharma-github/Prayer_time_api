# azanAPI

azanAPI is a stateless, versioned REST API for calculating Islamic prayer times and final Azan times. It accepts explicit coordinates, an IANA timezone, a local date, and calculation preferences, making it suitable for web applications, mobile clients, automations, and Home Assistant.

The API uses [adhanpy](https://github.com/alphahm/adhanpy) for astronomical calculations. It does not infer a timezone from coordinates, store request data, or require an external prayer-times service.

## Features

- Single-day and inclusive date-range prayer-time endpoints
- Eleven calculation methods, Shafi and Hanafi Asr calculations, and high-latitude rules
- Explicit IANA timezone handling and local `HH:MM` results
- Separate immutable calculated times and optional per-prayer Azan adjustments
- Predictable JSON error responses and generated OpenAPI documentation
- Docker image that runs as a non-root user and exposes a health check
- Home Assistant REST sensor and automation examples

## Quick start

Prerequisites: Python 3.11 or later and `pip`.

```bash
git clone <repository-url>
cd azanAPI

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

The service is then available at `http://127.0.0.1:8000`.

| Resource | Local URL |
| --- | --- |
| Interactive API documentation | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |
| OpenAPI document | `http://127.0.0.1:8000/openapi.json` |
| Health check | `http://127.0.0.1:8000/health` |

## API overview

All public prayer endpoints are versioned under `/api/v1`.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/prayer-times` | Calculate times for one local calendar date. |
| `GET` | `/api/v1/prayer-times/range` | Calculate times for an inclusive range of up to 366 local dates. |

### Calculate one day

```bash
curl --get http://127.0.0.1:8000/api/v1/prayer-times \
  --data-urlencode latitude=25.2048 \
  --data-urlencode longitude=55.2708 \
  --data-urlencode timezone=Asia/Dubai \
  --data-urlencode date=2026-09-15 \
  --data-urlencode calculation_method=dubai \
  --data-urlencode isha_adjustment=10
```

The response includes the settings actually used, the raw astronomical values, and the final Azan values. Azan adjustments never modify `calculated_times`.

```json
{
  "date": "2026-09-15",
  "timezone": "Asia/Dubai",
  "coordinates": { "latitude": 25.2048, "longitude": 55.2708 },
  "calculation_method": "dubai",
  "madhab": "shafi",
  "high_latitude_rule": "middle_of_the_night",
  "calculated_times": {
    "fajr": "04:47", "sunrise": "06:01", "dhuhr": "12:17",
    "asr": "15:43", "sunset": "18:22", "maghrib": "18:25", "isha": "19:39"
  },
  "azan_times": {
    "fajr": "04:47", "dhuhr": "12:17", "asr": "15:43",
    "maghrib": "18:25", "isha": "19:49"
  },
  "adjustments_minutes": {
    "fajr": 0, "dhuhr": 0, "asr": 0, "maghrib": 0, "isha": 10
  }
}
```

The example demonstrates the response format. Prayer times vary according to the requested date, location, timezone, and calculation settings.

### Request parameters

`/api/v1/prayer-times` requires `latitude`, `longitude`, `timezone`, and `calculation_method`. `date` is optional and defaults to the current date in the requested timezone.

| Parameter | Rules | Default |
| --- | --- | --- |
| `latitude` | Decimal number from `-90` to `90` | — |
| `longitude` | Decimal number from `-180` to `180` | — |
| `timezone` | IANA timezone, such as `Asia/Dubai` | — |
| `date` | Gregorian `YYYY-MM-DD` | Today in the requested timezone |
| `calculation_method` | One of the supported methods below | — |
| `madhab` | `shafi` or `hanafi` | `shafi` |
| `high_latitude_rule` | `middle_of_the_night`, `seventh_of_the_night`, or `twilight_angle` | `middle_of_the_night` |
| `fajr_adjustment`, `dhuhr_adjustment`, `asr_adjustment`, `maghrib_adjustment`, `isha_adjustment` | Whole minutes from `-1440` to `1440` | `0` |

Supported calculation methods: `muslim_world_league`, `egyptian`, `karachi`, `umm_al_qura`, `dubai`, `moon_sighting_committee`, `north_america`, `kuwait`, `qatar`, `singapore`, and `uoif`.

Sunrise and sunset are returned only in `calculated_times`; they are not Azan prayers and cannot be adjusted. An adjustment can cross midnight, but v1 returns bare `HH:MM` strings, so clients scheduling an adjusted time should account for rollover.

### Range requests

Use `/api/v1/prayer-times/range` with the same settings as the single-day endpoint, replacing `date` with required `start_date` and `end_date` values. Both dates are included, the limit is 366 days, and results are in chronological order.

```bash
curl --get http://127.0.0.1:8000/api/v1/prayer-times/range \
  --data-urlencode latitude=25.2048 \
  --data-urlencode longitude=55.2708 \
  --data-urlencode timezone=Asia/Dubai \
  --data-urlencode start_date=2026-09-15 \
  --data-urlencode end_date=2026-09-17 \
  --data-urlencode calculation_method=dubai
```

### Errors and compatibility

Invalid request values return `422` with a stable `error` envelope. Valid requests that cannot be calculated—for example, an unknown timezone—return `400`.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [{ "field": "query.latitude", "message": "...", "type": "..." }]
  }
}
```

The `/api/v1` prefix is part of the public contract. Backward-incompatible changes to fields, defaults, enums, validation, or error shapes require a new API version. Refer to `/docs` or `/openapi.json` for the complete current contract.

## Configuration

Configuration is read from environment variables. Copy `.env.example` when you need to record local values; environment loading is managed by your process runner.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `Prayer Timing API` | Service name shown in API metadata. |
| `APP_VERSION` | `0.1.0` | Service version shown in API metadata. |
| `APP_ENVIRONMENT` | `development` | Environment label for logs. |
| `APP_DEBUG` | `false` | Enables debug-level logging when true. |
| `LOG_LEVEL` | `INFO` | Standard Python log level. |

## Docker

Build and run a production-style local container:

```bash
docker build -t azanapi:latest .
docker run --rm -p 8000:8000 -e LOG_LEVEL=INFO azanapi:latest
```

The container listens on port `8000`, runs as a non-root user, and includes a health check against `/health`.

## Documentation site and Home Assistant

The standalone documentation site lives in [Prayer_time_api_docs](Prayer_time_api_docs/README.md). It contains expanded API guides, examples in cURL, Python, and JavaScript, and deployment documentation.

Home Assistant examples are available in [examples/home-assistant](examples/home-assistant/README.md), with a full guide in [docs/home-assistant.md](docs/home-assistant.md).

## Development

Run the quality checks before opening a pull request:

```bash
pytest -q
ruff check .
ruff format --check .
```

To format the project:

```bash
ruff format .
```

## Contributing

Contributions are welcome. Bug reports, documentation improvements, tests, and well-scoped features all help make azanAPI more useful.

1. Open an issue to discuss a substantial change before investing implementation time.
2. Create a focused branch and keep unrelated refactors out of the change.
3. Add or update tests and documentation for behavior or contract changes.
4. Run the verification commands above and submit a clear pull request.

Please preserve explicit timezone handling, the separation between astronomical and adjusted Azan times, and v1 compatibility guarantees.

## License

azanAPI is licensed under the [MIT License](LICENSE). You may use, modify, and redistribute it under the terms in that file.

## Acknowledgements

Prayer-time calculations are provided by [adhanpy](https://github.com/alphahm/adhanpy), based on the Adhan calculation project by [Batoul Apps](https://github.com/batoulapps/Adhan).
