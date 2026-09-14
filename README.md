# AzanAPI

A production-oriented Islamic prayer and Azan timing REST API designed for Home Assistant and other clients.

The service calculates prayer times from geographic coordinates, date, timezone, calculation method, Madhab, and high-latitude rules. The calculation engine is currently based on `adhanpy`, a Python implementation derived from the Batoul Apps Adhan project.

## Project status

Current phase: **Phase 3**

Completed:

- Phase 0: requirements, architecture, calculation-library evaluation
- Phase 1: project foundation and FastAPI application skeleton
- Phase 2: verified prayer calculation engine
- Phase 3: public FastAPI prayer-times endpoint

Phase 3 verification currently has:

```text
15 passed, 2 warnings
```

`ruff check .` passes.

`ruff format --check .` currently reports formatting differences in three files. Run `ruff format .` before committing.

The two pytest warnings are dependency-stack deprecation warnings from FastAPI/Starlette's test-client stack. They do not currently cause test failures.

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

Install dependencies:

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

Current public endpoint:

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

Example:

```bash
curl "http://127.0.0.1:8000/api/v1/prayer-times?latitude=35.775&longitude=-78.6336&timezone=America/New_York&date=2015-07-12&calculation_method=north_america&madhab=hanafi"
```

Expected response:

```json
{
  "date": "2015-07-12",
  "timezone": "America/New_York",
  "coordinates": {
    "latitude": 35.775,
    "longitude": -78.6336
  },
  "calculation_method": "north_america",
  "madhab": "hanafi",
  "high_latitude_rule": "middle_of_the_night",
  "times": {
    "fajr": "04:42",
    "sunrise": "06:08",
    "dhuhr": "13:21",
    "asr": "18:22",
    "sunset": "20:32",
    "maghrib": "20:32",
    "isha": "21:57"
  }
}
```

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

Invalid FastAPI/Pydantic request parameters return:

```text
HTTP 422
```

Unknown IANA timezones return:

```text
HTTP 400
```

Example:

```json
{
  "detail": "Unknown IANA timezone: Not/ARealTimezone"
}
```

Calculation-layer `ValueError` conditions are converted into HTTP 400 responses.

---

# Testing

Run the complete suite:

```bash
pytest -q
```

Current Phase 3 result:

```text
15 passed, 2 warnings
```

The warnings are from the current FastAPI/Starlette test-client dependency stack:

- Starlette warning about the `httpx` test client integration
- AnyIO deprecation warning involving `BlockingPortal`

They do not currently fail tests.

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

Before committing Phase 3, run:

```bash
ruff format .
pytest -q
ruff check .
ruff format --check .
```

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

## Separate calculated and future adjusted times

The current engine produces the calculated prayer times.

Future phases can layer configurable Azan adjustments on top without modifying the astronomical calculation itself.

Conceptually:

```text
Calculated prayer time
        +
Configured Azan adjustment
        =
Final Azan time
```

This distinction should remain explicit in the architecture.

---

# Planned future phases

The project is intentionally being implemented incrementally.

## Phase 4

Planned areas:

- Azan/time adjustments
- calculated versus final Azan time distinction
- richer response structure
- production-oriented request behavior
- additional validation where required

## Later phases

Potential future work includes:

- monthly prayer times
- yearly prayer times
- additional query capabilities
- production logging improvements
- Docker
- HTTPS deployment
- VPS deployment
- Home Assistant integration
- operational health/readiness behavior
- production security configuration

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

Phase 3:

```text
pytest: 15 passed
ruff check: passing
ruff format --check: needs formatting cleanup
```

Before Phase 3 approval:

```bash
ruff format .
pytest -q
ruff check .
ruff format --check .
```

---

# Phase gate

Each phase must be explicitly reviewed and approved before implementation of the next phase.

Current state:

```text
Phase 0: COMPLETE
Phase 1: APPROVED
Phase 2: APPROVED
Phase 3: IMPLEMENTATION COMPLETE, FINAL VERIFICATION PENDING
Phase 4: NOT STARTED
```

Do not begin Phase 4 until Phase 3 has been reviewed and explicitly approved.

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
