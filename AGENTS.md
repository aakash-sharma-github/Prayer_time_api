# azanAPI — Agent Guide

## Purpose and scope

azanAPI is a stateless FastAPI service that calculates Islamic prayer times and final
Azan times. It is designed for general HTTP clients and Home Assistant. This repository
owns API behavior, its OpenAPI contract, calculation logic, tests, Docker image, and
Home Assistant REST/YAML examples.

Related repositories are intentionally separate:

- `Prayer_time_api_docs/` is the standalone Next.js/Nextra documentation site.
- `azanAPI-homeassistant/` is the Home Assistant OS app packaging repository. It must
  consume this repository at a pinned Git commit and must not duplicate `app/`.

Do not implement documentation-site or HA deployment changes in the API unless an API
contract or source-image change makes a coordinated update necessary.

## Architecture

```text
HTTP client → FastAPI route → request validation → domain model
            → PrayerCalculator (adhanpy adapter) → domain result
            → PrayerAdjustmentService → Pydantic response / JSON
```

- `app/main.py`: application factory, lifespan logging, and router registration.
- `app/api/`: HTTP routes and stable error handlers.
- `app/api/v1/prayer_times.py`: one-day endpoint.
- `app/api/v1/prayer_times_range.py`: inclusive multi-day endpoint.
- `app/domain/prayer.py`: application-owned enums and immutable domain dataclasses.
- `app/services/prayer_calculator.py`: the only adapter that should directly use
  `adhanpy` types and calculation APIs.
- `app/services/prayer_adjustments.py`: applies minute offsets without mutating the
  astronomical result.
- `app/services/prayer_range.py`: calculates each local date independently.
- `app/schemas/`: externally visible Pydantic response and error models.
- `tests/`: endpoint, domain/service, and OpenAPI-contract tests.

## Public API contract

Routes:

| Route | Behavior |
| --- | --- |
| `GET /` | Service metadata. |
| `GET /health` | Health endpoint used by Docker and Home Assistant. |
| `GET /api/v1/prayer-times` | One local calendar date. |
| `GET /api/v1/prayer-times/range` | Inclusive range, maximum 366 dates. |

Prayer routes require explicit `latitude`, `longitude`, `timezone` (IANA), and
`calculation_method`. One-day requests accept optional `date`; range requests require
`start_date` and `end_date`. Defaults are `madhab=shafi` and
`high_latitude_rule=middle_of_the_night`.

Supported calculation methods are `muslim_world_league`, `egyptian`, `karachi`,
`umm_al_qura`, `dubai`, `moon_sighting_committee`, `north_america`, `kuwait`,
`qatar`, `singapore`, and `uoif`. Madhabs are `shafi` and `hanafi`; high-latitude
rules are `middle_of_the_night`, `seventh_of_the_night`, and `twilight_angle`.

Successful responses contain immutable `calculated_times`, separately adjusted
`azan_times`, and `adjustments_minutes`. Only Fajr, Dhuhr, Asr, Maghrib, and Isha
are adjustable (`-1440` through `1440` minutes). Sunrise and sunset are calculation
values only. All times are local bare `HH:MM` strings; an adjustment may cross
midnight, so clients must handle that rollover when scheduling.

Errors always use a top-level `error` envelope. Invalid input is `422` with
`VALIDATION_ERROR` and field details; a valid but uncalculable request, such as an
unknown IANA zone, is `400` (for example `INVALID_TIMEZONE`).

## Non-negotiable rules

- Never hard-code a location, timezone, or server-local timezone.
- Never infer a timezone from coordinates; callers must supply an IANA timezone.
- Keep `adhanpy` classes inside the calculation adapter; do not expose them in API
  schemas or routes.
- Keep calculated and adjusted Azan times separate. Do not apply adjustments inside
  `PrayerCalculator`.
- Preserve the v1 contract. Changes to existing field names/types/meaning, defaults,
  enums, bounds, status codes, or error shape require an explicitly approved new API
  version (for example `/api/v2`).
- Keep the service stateless: no database, persistence, authentication, caching, or
  location lookup unless separately approved.
- `adhanpy` treats dates through UTC. Preserve the UTC-noon technique in
  `PrayerCalculator` so positive-offset zones retain the requested local date.

## Development workflow

Use Python 3.11+; the production image uses Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Useful local URLs: `/docs`, `/redoc`, `/openapi.json`, and `/health` on port 8000.
Environment defaults are defined in `app/core/config.py`; see `.env.example`.

Before submitting an API change, run:

```bash
pytest -q
ruff check .
ruff format --check .
```

Use `ruff format .` only when formatting changes are intended. Add tests for every
behavior change; update `tests/test_openapi_contract.py` deliberately for approved
contract changes.

## Docker and Home Assistant coordination

The root `Dockerfile` is the API's production container reference: it runs as a
non-root user, serves port 8000, and health-checks `/health`.

The Home Assistant packaging repository builds from a pinned commit of this
repository. When an API revision should be deployed there:

1. Commit and push the API change.
2. Update `AZANAPI_REF` in `azanAPI-homeassistant/azanapi/Dockerfile` to that commit.
3. Increment the Home Assistant app `version` in its `config.yaml`.
4. Build and test the HA app, including `/health`, both v1 prayer endpoints, and an
   invalid-timezone response.

## Documentation coordination

The documentation site treats this API's `/openapi.json` as the contract source of
truth. For API changes, update the relevant MDX guides in `Prayer_time_api_docs/`,
run its `npm run sync:openapi` against this server, and confirm `npm run build`.

## Change checklist

1. Identify whether the change is internal, additive v1, or breaking.
2. Update domain models, services, schemas, routes, and tests in that order when
   applicable.
3. Keep OpenAPI descriptions/examples accurate.
4. Update API README and docs site for user-visible changes.
5. Run all Python checks; build Docker when container behavior changes.
