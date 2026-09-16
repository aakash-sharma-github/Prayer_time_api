# AzanAPI

A production-oriented Islamic prayer and Azan timing REST API designed for Home Assistant and other clients.

The service calculates prayer times from geographic coordinates, date, timezone, calculation method, Madhab, and high-latitude rules. The calculation engine is currently based on `adhanpy`, a Python implementation derived from the Batoul Apps Adhan project.

## Project status

Current phase: **Phase 9**

Completed:

- Phase 0: requirements, architecture, calculation-library evaluation
- Phase 1: project foundation and FastAPI application skeleton
- Phase 2: verified prayer calculation engine
- Phase 3: public FastAPI prayer-times endpoint
- Phase 4: calculated-vs-Azan time distinction and configurable per-prayer adjustments
- Phase 5: predictable API error responses and validation-error handling
- Phase 6: v1 API contract finalization and documentation
- Phase 7: inclusive multi-date prayer-times range endpoint
- Phase 8: Home Assistant REST/YAML documentation and examples
- Phase 9: production Docker containerization

Phase 4 verification currently has:

```text
19 passed, 2 warnings
```

`ruff check .` passes. `ruff format --check .` passes.

The two pytest warnings are dependency-stack deprecation warnings from FastAPI/Starlette's test-client stack. They do not currently cause test failures.

### Bug-fix note (pre-Phase-4-approval review)

A codebase review before Phase 4 sign-off found the endpoint in an inconsistent, non-functional state: the domain/service/schema layers for Azan adjustments had already been written, but `app/api/v1/prayer_times.py` still returned the old Phase 3 response shape (`times`) instead of the new `calculated_times` / `azan_times` / `adjustments_minutes` shape, and never called `PrayerAdjustmentService`. Every request to `/api/v1/prayer-times` was failing with a `pydantic.ValidationError`. Separately, `adhanpy` was missing from `pyproject.toml`, so a clean `pip install -e .` would not install the calculation engine at all. Both are fixed as part of this phase; see "Fixed in this review" below.

### Fixed in this review

1. **`app/api/v1/prayer_times.py` — broken response construction.** The endpoint now builds `PrayerAdjustments` from the five `*_adjustment` query parameters, calls `_adjustment_service.apply(result, adjustments)`, and constructs `calculated_times` / `azan_times` / `adjustments_minutes` matching the actual `PrayerTimesResponse` schema. This was previously untested end-to-end; it now is (see `tests/test_prayer_api.py`).
2. **`pyproject.toml` — missing `adhanpy` runtime dependency.** Added `adhanpy>=1.0,<2.0` to `[project.dependencies]`.
3. **`README.md` — installation instructions.** Previously only documented `pip install -r requirements-dev.txt`, which installs pytest/httpx/Ruff but not FastAPI/Uvicorn/adhanpy. Now documents `pip install -e .` as the runtime-dependency step, run before the dev-tools step.
4. **Lint cleanup** (`ruff check --fix` + `ruff format`): unsorted import blocks in `app/domain/prayer.py` and `app/api/v1/prayer_times.py`, an unused `PrayerAdjustments` import, an unused `pydantic.Field` import in `app/schemas/prayer.py`, and inconsistent parameter indentation. `ruff check .` and `ruff format --check .` both pass cleanly.
5. **`tests/test_prayer_api.py` — updated for the real response contract** and extended with four new Phase 4 tests (adjustment applied/untouched-fields check, negative adjustment, midnight rollover, out-of-range 422).

---

## Goals

The API is being built with the following goals:

1. Provide reliable Islamic prayer times as a stateless HTTPS REST API.
2. Support dynamic latitude and longitude.
3. Require an explicit IANA timezone instead of guessing one.
4. Support multiple calculation methods.
5. Support Shafi and Hanafi Asr calculations.
6. Support high-latitude calculation rules.
7. Return Fajr, Sunrise, Dhuhr, Asr, Sunset, Maghrib, and Isha.
8. Keep astronomical/calculated times separate from future Azan adjustments.
9. Provide strict validation and useful HTTP errors.
10. Provide OpenAPI/Swagger documentation through FastAPI.
11. Remain suitable for Raspberry Pi/Home Assistant clients while running centrally on a VPS.
12. Avoid a database initially. The service is intentionally stateless.

---

## Architecture

```text
Home Assistant
      |
      | HTTPS / JSON
      v
FastAPI REST API
      |
      | validated domain request
      v
PrayerCalculator
      |
      | isolated adapter
      v
adhanpy
      |
      v
Astronomical prayer calculation
```

The internal calculation layer does not expose `adhanpy` classes to the API.

The architecture separates:

```text
API request
    ->
domain request
    ->
calculation engine
    ->
domain result
    ->
API response
```

This keeps the external API stable if the calculation library changes later.

---

## Current project structure

```text
azanAPI/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── prayer_times.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   ├── domain/
│   │   ├── __init__.py
│   │   └── prayer.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── prayer.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── prayer_calculator.py
│   └── main.py
├── tests/
│   ├── test_health.py
│   ├── test_prayer_api.py
│   └── test_root.py
├── .venv/
├── pyproject.toml
├── requirements-dev.txt
└── README.md
```

`.venv/` should not be committed.

---

# Development environment

The project has been developed and verified in:

- Fedora Linux
- Python 3.14.7
- FastAPI
- Uvicorn
- pytest
- Ruff
- `adhanpy`
- Python `zoneinfo`

Create/use the virtual environment:

```bash
cd ~/Data/Projects/azanAPI

python3 -m venv .venv
source .venv/bin/activate
```

If the environment already exists:

```bash
source .venv/bin/activate
```

Install the application and its runtime dependencies (FastAPI, Uvicorn, `adhanpy`):

```bash
pip install -e .
```

Install development tools (pytest, httpx, Ruff):

```bash
pip install -r requirements-dev.txt
```

---

# Running the application

Development server:

```bash
uvicorn app.main:app --reload
```

Default development URL:

```text
http://127.0.0.1:8000
```

Root endpoint:

```text
GET /
```

Health endpoint:

```text
GET /health
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

---

# Phase 0: Research and architecture

Phase 0 established the requirements and selected the calculation engine.

The selected library is:

```text
adhanpy
```

Reason for selection:

- Offline calculation
- Python implementation
- Based on Batoul Apps Adhan calculation logic
- Multiple calculation methods
- Madhab support
- High-latitude rules
- Timezone-aware output
- No external API dependency for prayer calculations

Official references:

- Batoul Apps Adhan: https://github.com/batoulapps/Adhan
- adhanpy: https://github.com/alphahm/adhanpy
- PyPI: https://pypi.org/project/adhanpy/
- Adhan JS methods documentation: https://github.com/batoulapps/adhan-js/blob/master/METHODS.md
- Adhan Kotlin prayer-time test source: https://github.com/batoulapps/adhan-kotlin/blob/main/adhan/src/commonTest/kotlin/com/batoulapps/adhan2/PrayerTimesTest.kt

Important implementation rule:

**Do not hard-code Dubai, UAE, or any other location/timezone.**

The location and timezone must come from the request.

---

# Phase 1: Project foundation

Phase 1 created the FastAPI project structure.

Initial responsibilities:

- Application entry point
- Configuration
- Logging
- Health endpoint
- Root endpoint
- Development server
- pytest setup
- Ruff setup

Phase 1 verification:

```text
4 passed
```

Ruff was also brought to a clean state.

The existing health/root tests remain part of the complete test suite.

---

# Phase 2: Prayer calculation engine

Phase 2 implemented the internal calculation layer.

## Domain models

`app/domain/prayer.py`

Defines:

- `CalculationMethodName`
- `MadhabName`
- `HighLatitudeRuleName`
- `PrayerCalculationRequest`
- `PrayerTimesResult`

The domain layer intentionally does not expose `adhanpy` implementation classes.

## Calculation service

`app/services/prayer_calculator.py`

Responsibilities:

- Validate latitude/longitude
- Map public method names to `adhanpy`
- Map Madhab
- Map high-latitude rule
- Preserve requested calendar dates
- Use explicit `ZoneInfo`
- Calculate prayer times
- Calculate astronomical sunset
- Return timezone-aware `datetime` values

### Important timezone handling

`adhanpy` internally converts the supplied date through UTC.

For that reason, the application passes the requested calendar date at UTC noon rather than local midnight.

This prevents a positive-offset timezone such as `Asia/Dubai` from rolling the requested date into the previous UTC date.

The internal result keeps real timezone-aware `datetime` objects.

Formatting into `"HH:MM"` happens only at the API response boundary.

---

# Supported calculation methods

The installed `adhanpy` implementation exposes:

| Public name | Method |
|---|---|
| `muslim_world_league` | Muslim World League |
| `egyptian` | Egyptian |
| `karachi` | Karachi |
| `umm_al_qura` | Umm Al-Qura |
| `dubai` | Dubai |
| `moon_sighting_committee` | Moon Sighting Committee |
| `north_america` | North America |
| `kuwait` | Kuwait |
| `qatar` | Qatar |
| `singapore` | Singapore |
| `uoif` | UOIF |

The library's internal `NONE` method is deliberately not exposed as a normal public API option.

---

# Madhab

Supported values:

```text
shafi
hanafi
```

The Madhab primarily affects Asr shadow-length calculation.

A verified reference case produced:

```text
Shafi:
Asr = 17:09

Hanafi:
Asr = 18:22
```

---

# High-latitude rules

Supported values:

```text
middle_of_the_night
seventh_of_the_night
twilight_angle
```

These are mapped to the corresponding `adhanpy` calculation rules internally.

---

# Prayer values

The internal result contains:

```text
fajr
sunrise
dhuhr
asr
sunset
maghrib
isha
```

The distinction between `sunset` and `maghrib` is intentional.

- `sunset` is the astronomical sunset calculated through `adhanpy`'s `SolarTime`.
- `maghrib` is the calculated prayer time returned by `PrayerTimes`.

The public API currently formats both as local `HH:MM` strings.

---

# Phase 2 reference verification

The following official-style reference case was used:

```text
Latitude:          35.7750
Longitude:         -78.6336
Date:              2015-07-12
Timezone:          America/New_York
Calculation method: North America
Madhab:             Hanafi
```

Expected and verified result:

```text
Fajr      04:42
Sunrise   06:08
Dhuhr     13:21
Asr       18:22
Maghrib   20:32
Isha      21:57
```

Sunset is independently obtained from the same underlying astronomical calculation implementation.

---

# Phase 3: REST API

Phase 3 introduced the public endpoint:

```text
GET /api/v1/prayer-times
```

with `latitude`, `longitude`, `timezone`, `date`, `calculation_method`, `madhab`, and `high_latitude_rule` query parameters, and a response distinguishing coordinates/method/madhab from the calculated prayer times. Phase 4 (below) extended this same endpoint with Azan adjustments; the response shape documented here is the current, Phase-4 shape.

---

# Phase 4: Calculated vs. Azan time, and configurable adjustments

Phase 4 adds the distinction the architecture always intended: the astronomically **calculated** prayer time is never mutated, and a separately reported **Azan** time is the calculated time plus a caller-supplied per-prayer offset in minutes.

Endpoint (unchanged path from Phase 3):

```text
GET /api/v1/prayer-times
```

Query parameters:

| Parameter | Required | Description |
|---|---|---|
| `latitude` | yes | Decimal latitude, -90 to 90 |
| `longitude` | yes | Decimal longitude, -180 to 180 |
| `timezone` | yes | IANA timezone |
| `date` | no | Gregorian date, defaults to today in requested timezone |
| `calculation_method` | yes | Calculation method |
| `madhab` | no | Defaults to `shafi` |
| `high_latitude_rule` | no | Defaults to `middle_of_the_night` |
| `fajr_adjustment` | no | Minutes to add to Fajr's Azan time. Defaults to `0`. Range: -1440 to 1440. |
| `dhuhr_adjustment` | no | Same, for Dhuhr. |
| `asr_adjustment` | no | Same, for Asr. |
| `maghrib_adjustment` | no | Same, for Maghrib. |
| `isha_adjustment` | no | Same, for Isha. |

Sunrise and sunset have no Azan and therefore no adjustment parameter — they only appear in `calculated_times`.

Example:

```bash
curl "http://127.0.0.1:8000/api/v1/prayer-times?latitude=25.2048&longitude=55.2708&timezone=Asia/Dubai&date=2026-09-14&calculation_method=dubai&isha_adjustment=90"
```

Response:

```json
{
  "date": "2026-09-14",
  "timezone": "Asia/Dubai",
  "coordinates": {
    "latitude": 25.2048,
    "longitude": 55.2708
  },
  "calculation_method": "dubai",
  "madhab": "shafi",
  "high_latitude_rule": "middle_of_the_night",
  "calculated_times": {
    "fajr": "04:47",
    "sunrise": "06:01",
    "dhuhr": "12:18",
    "asr": "15:45",
    "sunset": "18:24",
    "maghrib": "18:27",
    "isha": "19:42"
  },
  "azan_times": {
    "fajr": "04:47",
    "dhuhr": "12:18",
    "asr": "15:45",
    "maghrib": "18:27",
    "isha": "21:12"
  },
  "adjustments_minutes": {
    "fajr": 0,
    "dhuhr": 0,
    "asr": 0,
    "maghrib": 0,
    "isha": 90
  }
}
```

`calculated_times.isha` (19:42) is untouched; `azan_times.isha` (21:12) is the calculated time plus the requested 90-minute offset. This response was produced by the live application, not hand-written.

## Midnight-rollover behavior (explicit design decision)

An adjustment can legitimately push an Azan time past midnight — for example, a large positive Isha adjustment near 23:xx. `azan_times.*` values are computed as timezone-aware `datetime + timedelta(minutes=...)`, so the rollover arithmetic itself is correct: adding 150 minutes to `21:57` correctly produces `00:27` on the following calendar day.

However, in this version the response's top-level `date` field always reflects the **requested** calculation date, and each `azan_times` entry is formatted as a bare `HH:MM` string with no date attached. This means an Azan time that has rolled into the next calendar day is not distinguishable, from the response alone, from one that did not roll over — a client would need to independently know that `isha_adjustment` was large enough to cross midnight.

This is called out explicitly rather than silently shipped: v1 does not attempt to represent the rolled-over calendar date in the response. If a Home Assistant integration needs to schedule an Azan trigger that may land on the next day, that must currently be handled client-side (e.g. by comparing the adjusted `HH:MM` against `calculated_times.isha` and rolling the scheduling day forward if the adjusted value is numerically earlier). A future, explicitly-approved phase could add an ISO-8601 timestamp (date + time) per Azan entry instead of a bare `HH:MM` string if this becomes a real requirement — that would be a breaking `v1` contract change and is intentionally out of scope here.

Rollover arithmetic is covered by `tests/test_prayer_api.py::test_isha_adjustment_can_roll_over_midnight`.

---

# Validation and errors

Latitude is constrained to:

```text
-90 <= latitude <= 90
```

Longitude is constrained to:

```text
-180 <= longitude <= 180
```

Every error response has a top-level `error` object with a stable machine-readable
`code` and a human-readable `message`.

Invalid FastAPI/Pydantic request parameters return HTTP 422:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "query.latitude",
        "message": "Input should be less than or equal to 90",
        "type": "less_than_equal"
      }
    ]
  }
}
```

The `details` list identifies every invalid request field. Its `field` value uses
the FastAPI request location followed by the field name, such as `query.latitude`.

Unknown IANA timezones and calculation-layer errors return HTTP 400. Example:

```json
{
  "error": {
    "code": "INVALID_TIMEZONE",
    "message": "Unknown IANA timezone: Not/ARealTimezone"
  }
}
```

Both response types are documented on `GET /api/v1/prayer-times` in OpenAPI.

---

# Phase 6: v1 API contract and documentation

Phase 6 finalizes the public v1 contract before any deployment or infrastructure work.
The interactive contract is available at `/docs`, with the machine-readable OpenAPI
document at `/openapi.json`. The rules below are the authoritative human-readable
summary of that same contract.

## v1 endpoint contract

`GET /api/v1/prayer-times` calculates one day's prayer times for explicitly supplied
coordinates, timezone, and calculation method. It has no side effects and does not
persist request data.

| Parameter | Required | Type and allowed values | Default |
|---|---:|---|---|
| `latitude` | yes | Number from `-90` through `90` | — |
| `longitude` | yes | Number from `-180` through `180` | — |
| `timezone` | yes | Valid IANA timezone, e.g. `Asia/Dubai` | — |
| `date` | no | Gregorian `YYYY-MM-DD` date | Today in the requested timezone |
| `calculation_method` | yes | One of the supported calculation methods | — |
| `madhab` | no | `shafi`, `hanafi` | `shafi` |
| `high_latitude_rule` | no | `middle_of_the_night`, `seventh_of_the_night`, `twilight_angle` | `middle_of_the_night` |
| `fajr_adjustment` | no | Whole minutes from `-1440` through `1440` | `0` |
| `dhuhr_adjustment` | no | Whole minutes from `-1440` through `1440` | `0` |
| `asr_adjustment` | no | Whole minutes from `-1440` through `1440` | `0` |
| `maghrib_adjustment` | no | Whole minutes from `-1440` through `1440` | `0` |
| `isha_adjustment` | no | Whole minutes from `-1440` through `1440` | `0` |

The accepted calculation methods are: `muslim_world_league`, `egyptian`, `karachi`,
`umm_al_qura`, `dubai`, `moon_sighting_committee`, `north_america`, `kuwait`,
`qatar`, `singapore`, and `uoif`.

A successful `200` response contains the requested date/timezone and coordinates,
the selected calculation options, immutable astronomical `calculated_times`, adjusted
`azan_times`, and the supplied `adjustments_minutes`. All time values are local
`HH:MM` strings. `calculated_times` has Fajr, Sunrise, Dhuhr, Asr, Sunset, Maghrib,
and Isha; `azan_times` has only Fajr, Dhuhr, Asr, Maghrib, and Isha. Sunrise and
sunset are never adjustable.

Example request:

```bash
curl --get http://127.0.0.1:8000/api/v1/prayer-times \
  --data-urlencode latitude=25.2048 \
  --data-urlencode longitude=55.2708 \
  --data-urlencode timezone=Asia/Dubai \
  --data-urlencode date=2026-09-14 \
  --data-urlencode calculation_method=dubai \
  --data-urlencode isha_adjustment=90
```

For a complete successful response example, see the [Azan adjustments](#phase-4-calculated-vs-azan-time-and-configurable-adjustments)
section above or the `200` response example in `/docs`.

`400` means a syntactically valid request could not be calculated, such as an unknown
IANA timezone. `422` means one or more input values failed validation. Both use the
top-level `error` envelope documented in [Validation and errors](#validation-and-errors);
only `422` includes the per-field `details` list.

## Versioning rules

The `/api/v1` prefix is part of the public contract. Additive, backward-compatible
documentation or optional capabilities may be introduced within v1 only when they do
not alter existing meanings, defaults, validation behavior, response fields, or error
envelopes. Removing or renaming a field, changing a field type or meaning, changing a
default/range/enum, or changing an error shape requires a new versioned path such as
`/api/v2/...`. Existing v1 behavior remains supported for its published lifetime.

The OpenAPI contract tests in `tests/test_openapi_contract.py`, alongside endpoint
behavior tests, are required checks for v1 changes. Update them deliberately whenever
an explicitly approved contract change is made.

Phase 6 intentionally adds no Docker, VPS, HTTPS, reverse proxy, authentication,
database, caching, Home Assistant integration, or monthly/yearly endpoints.

---

# Phase 7: date-range prayer times

`GET /api/v1/prayer-times/range` returns independently calculated prayer times for
an inclusive local-date range while leaving `GET /api/v1/prayer-times` unchanged.
It accepts the same location, calculation, and Azan-adjustment options as the
single-day endpoint, replacing `date` with required `start_date` and `end_date`
(`YYYY-MM-DD`).

The range must contain between one and 366 dates, inclusive. Results are always
chronological and each date is calculated separately using the requested timezone;
the API does not derive a range from a UTC sequence. A reversed range returns:

```json
{
  "error": {
    "code": "INVALID_DATE_RANGE",
    "message": "start_date must be on or before end_date"
  }
}
```

More than 366 requested dates returns `400` with `DATE_RANGE_TOO_LARGE`. The
response repeats shared request configuration once at the top level, including
`adjustments_minutes`; every `days` entry contains only `date`, `calculated_times`,
and `azan_times`. Adjustment semantics—including non-adjustable sunrise/sunset and
possible bare-`HH:MM` midnight rollover—are unchanged from the single-day contract.

Example:

```bash
curl --get http://127.0.0.1:8000/api/v1/prayer-times/range \
  --data-urlencode latitude=25.2048 \
  --data-urlencode longitude=55.2708 \
  --data-urlencode timezone=Asia/Dubai \
  --data-urlencode start_date=2026-09-15 \
  --data-urlencode end_date=2026-09-17 \
  --data-urlencode calculation_method=dubai
```

The full range schema and success/error examples are available in `/docs` and
`/openapi.json`. Phase 7 does not add monthly/yearly endpoints, pagination,
exports, caching, background jobs, authentication, location lookup, new calculation
methods, or deployment infrastructure.

---

# Phase 8: Home Assistant REST/YAML examples

Phase 8 documents Home Assistant as a standard HTTP client of azanAPI. It adds no
custom Home Assistant component, Python code, config flow, HACS repository, or
Home Assistant dependency to the application.

See [Home Assistant integration](docs/home-assistant.md) for the full setup guide,
and [examples/home-assistant](examples/home-assistant) for copy/paste-ready REST
sensor and automation YAML. The single-date endpoint is the primary source for daily
entities; the date-range endpoint is an optional advanced use case.

---

# Testing

Run the complete suite:

```bash
pytest -q
```

Current project test collection:

```text
48 tests collected
```

Phase 7 tests cover range behavior and OpenAPI contract tests protect both v1
endpoints. Phase 8 verifies YAML syntax and the documented API paths and JSON fields
against the existing v1 response contract.

The warnings are from the current FastAPI/Starlette test-client dependency stack:

- Starlette warning about the `httpx` test client integration
- AnyIO deprecation warning involving `BlockingPortal`

They do not currently fail tests.

---

# Phase 9: Docker containerization

Phase 9 packages the existing API as one production-only Docker image. It does not
change the HTTP API, calculation logic, Home Assistant examples, or v1 response
contracts. It does not add Docker Compose, a reverse proxy, HTTPS, deployment,
authentication, a database, or persistent storage.

The image uses `python:3.12-slim`, installs runtime dependencies from
`pyproject.toml`, writes logs to standard output/error, exposes port `8000`, runs as
a non-root `appuser`, and checks the real `GET /health` endpoint.

Build the local image:

```bash
docker build -t azanapi:latest .
```

Run it on the host's port 8000:

```bash
docker run --rm -p 8000:8000 -e LOG_LEVEL=INFO azanapi:latest
```

The container listens on `0.0.0.0:8000`; use `http://127.0.0.1:8000` from the host.
In another terminal, verify health and the public API:

```bash
curl http://127.0.0.1:8000/health

curl "http://127.0.0.1:8000/api/v1/prayer-times?latitude=25.2048&longitude=55.2708&timezone=Asia/Dubai&date=2026-09-15&calculation_method=dubai&madhab=shafi"

curl "http://127.0.0.1:8000/api/v1/prayer-times/range?latitude=25.2048&longitude=55.2708&timezone=Asia/Dubai&start_date=2026-09-15&end_date=2026-09-17&calculation_method=dubai"
```

For detached verification, use a named container:

```bash
docker run -d --name azanapi-test -p 8000:8000 -e LOG_LEVEL=INFO azanapi:latest
docker inspect --format='{{json .State.Health}}' azanapi-test
docker exec azanapi-test id
docker logs azanapi-test
docker stop azanapi-test
docker rm azanapi-test
```

The health check runs every 30 seconds after a 10-second start period. `LOG_LEVEL`
accepts standard Python logging levels such as `DEBUG`, `INFO`, `WARNING`, or `ERROR`.
It defaults to `INFO`, unless the existing `APP_DEBUG` setting is enabled. `.env`
files and development artifacts are excluded from the image build context.

---

# Formatting and linting

Run:

```bash
ruff check .
```

Format the entire project:

```bash
ruff format .
```

Verify formatting without changing files:

```bash
ruff format --check .
```

Recommended verification sequence:

```bash
pytest -q
ruff check .
ruff format --check .
```

As of this review, all three pass cleanly with no outstanding issues.

---

# Git workflow

Check current state:

```bash
git status
```

Review changes:

```bash
git diff
```

After formatting and testing:

```bash
git add .
```

Review staged changes:

```bash
git diff --cached
```

Commit the completed work:

```bash
git commit -m "feat: add prayer times calculation API"
```

Verify:

```bash
git status
git log -1 --oneline
```

If `.venv/` appears in Git status, do not commit it. Add an appropriate `.gitignore` before committing.

Suggested `.gitignore` entries:

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
.env
.env.*
```

---

# Development command reference

Activate environment:

```bash
source .venv/bin/activate
```

Start development server:

```bash
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest -q
```

Run Ruff:

```bash
ruff check .
```

Format:

```bash
ruff format .
```

Check formatting:

```bash
ruff format --check .
```

Inspect installed `adhanpy`:

```bash
pip show adhanpy
```

Inspect Python version:

```bash
python --version
```

---

# API documentation

Once the server is running:

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

FastAPI documentation:

https://fastapi.tiangolo.com/

---

# Design decisions

## Explicit timezone

The client supplies an IANA timezone.

Examples:

```text
Asia/Dubai
America/New_York
Europe/London
Asia/Kolkata
```

The API does not infer a timezone from coordinates.

## Stateless service

There is no database in the current architecture.

A request contains enough information to calculate the result.

This makes the API easy to deploy on a VPS and easy to consume from Home Assistant.

## Domain/API separation

`adhanpy` types stay inside the calculation adapter.

The public API uses application-owned enums and response models.

This prevents an external library's classes from becoming part of the API contract.

## Separate calculated and adjusted (Azan) times

The calculation engine (`PrayerCalculator`) produces only the astronomical `calculated_times`. It has no knowledge of adjustments.

A separate `PrayerAdjustmentService`/`PrayerAdjustments.apply()` layers the caller-supplied per-prayer minute offsets on top, producing `azan_times`. This keeps the astronomical calculation pure and independently testable, and matches the response distinction:

```text
Calculated prayer time
        +
Configured Azan adjustment
        =
Final Azan time
```

Sunrise and sunset are calculated values only; they have no Azan and are never adjusted.

---

# Planned future phases

The project is intentionally being implemented incrementally.

## Later phases

The following is a proposed roadmap only. Each phase requires separate definition and
approval before implementation:

1. Phase 9: Docker/containerization
2. Phase 10: VPS deployment and HTTPS
3. Phase 11: production observability and security
4. Phase 12: final production testing and release
5. Future Phase 13: native Home Assistant integration in a separate repository

No database is planned until a concrete requirement exists.

---

# Important implementation rules

Do not:

- hard-code Dubai
- hard-code the server timezone
- guess a user's timezone
- expose `adhanpy` classes directly through the API
- duplicate astronomical equations unnecessarily
- apply Azan adjustments inside the base astronomical calculation
- introduce a database without a demonstrated requirement
- skip deterministic calculation tests

Keep:

- timezone handling explicit
- calculations deterministic
- API responses versioned
- domain models independent of the third-party library
- tests around reference calculations
- calculation methods explicit
- API errors predictable

---

# Current verification record

Phase 1:

```text
pytest: 4 passed
ruff: passing
Uvicorn: verified
/docs: verified
/openapi.json: verified
```

Phase 2:

```text
pytest: 10 passed
ruff: passing
```

Phase 2 reference calculation:

```text
North America + Hanafi
Fajr      04:42
Sunrise   06:08
Dhuhr     13:21
Asr       18:22
Maghrib   20:32
Isha      21:57
```

Phase 3 (as re-verified during this review):

```text
pytest: 15 passed
ruff check: passing
ruff format --check: passing
```

Phase 4:

```text
pytest: 19 passed, 2 warnings
ruff check: passing
ruff format --check: passing
adhanpy: added to pyproject.toml dependencies (packaging bug fixed)
manual verification: GET /api/v1/prayer-times exercised against a live
  uvicorn instance with an isha_adjustment=90 offset; response confirmed
  calculated_times.isha unchanged and azan_times.isha correctly offset
```

---

# Phase gate

Each phase must be explicitly reviewed and approved before implementation of the next phase.

Current state:

```text
Phase 0: APPROVED
Phase 1: APPROVED
Phase 2: APPROVED
Phase 3: APPROVED (re-verified during this review)
Phase 4: APPROVED
Phase 5: APPROVED
Phase 6: APPROVED
Phase 7: APPROVED
Phase 8: APPROVED
Phase 9: IMPLEMENTATION COMPLETE, PENDING APPROVAL
```

Do not begin Phase 10 until Phase 9 has been reviewed and explicitly approved.

---

# Notes on dependency warnings

Current tests produce two warnings related to the installed FastAPI/Starlette/AnyIO/httpx test stack.

These warnings are not calculation failures.

Do not hide them with global warning filters.

When dependency versions are intentionally updated, rerun the entire test suite and verify that the test-client compatibility remains correct.

---

# License

No project license has been selected yet.

Add a license before publishing or distributing the project publicly.
