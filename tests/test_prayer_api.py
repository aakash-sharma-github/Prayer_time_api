from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_prayer_times_reference_case() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 35.775,
            "longitude": -78.6336,
            "timezone": "America/New_York",
            "date": "2015-07-12",
            "calculation_method": "north_america",
            "madhab": "hanafi",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["date"] == "2015-07-12"
    assert body["timezone"] == "America/New_York"
    assert body["calculation_method"] == "north_america"
    assert body["madhab"] == "hanafi"

    assert body["calculated_times"] == {
        "fajr": "04:42",
        "sunrise": "06:08",
        "dhuhr": "13:21",
        "asr": "18:22",
        "sunset": "20:32",
        "maghrib": "20:32",
        "isha": "21:57",
    }

    # With no adjustments requested, azan_times must equal calculated_times
    # (minus sunrise, which is not an Azan-triggering prayer).
    assert body["azan_times"] == {
        "fajr": "04:42",
        "dhuhr": "13:21",
        "asr": "18:22",
        "maghrib": "20:32",
        "isha": "21:57",
    }

    assert body["adjustments_minutes"] == {
        "fajr": 0,
        "dhuhr": 0,
        "asr": 0,
        "maghrib": 0,
        "isha": 0,
    }


def test_prayer_times_defaults_date_in_requested_timezone() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 25.2048,
            "longitude": 55.2708,
            "timezone": "Asia/Dubai",
            "date": "2026-09-14",
            "calculation_method": "dubai",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["date"] == "2026-09-14"
    assert body["timezone"] == "Asia/Dubai"


def test_unknown_timezone_returns_400() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 25.2048,
            "longitude": 55.2708,
            "timezone": "Not/ARealTimezone",
            "date": "2026-09-14",
            "calculation_method": "dubai",
        },
    )

    assert response.status_code == 400
    assert "Unknown IANA timezone" in response.json()["detail"]


def test_invalid_coordinates_return_422() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 100,
            "longitude": 55.2708,
            "timezone": "Asia/Dubai",
            "date": "2026-09-14",
            "calculation_method": "dubai",
        },
    )

    assert response.status_code == 422


def test_adjustments_shift_azan_times_but_not_calculated_times() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 35.775,
            "longitude": -78.6336,
            "timezone": "America/New_York",
            "date": "2015-07-12",
            "calculation_method": "north_america",
            "madhab": "hanafi",
            "fajr_adjustment": 5,
            "isha_adjustment": 10,
        },
    )

    assert response.status_code == 200

    body = response.json()

    # The astronomical calculation must never move.
    assert body["calculated_times"]["fajr"] == "04:42"
    assert body["calculated_times"]["isha"] == "21:57"

    # Only the requested Azan times move, by exactly the requested offset.
    assert body["azan_times"]["fajr"] == "04:47"
    assert body["azan_times"]["isha"] == "22:07"

    # Prayers with no adjustment stay equal to their calculated time.
    assert body["azan_times"]["dhuhr"] == body["calculated_times"]["dhuhr"]
    assert body["azan_times"]["asr"] == body["calculated_times"]["asr"]
    assert body["azan_times"]["maghrib"] == body["calculated_times"]["maghrib"]

    assert body["adjustments_minutes"] == {
        "fajr": 5,
        "dhuhr": 0,
        "asr": 0,
        "maghrib": 0,
        "isha": 10,
    }


def test_negative_adjustment_moves_azan_time_earlier() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 35.775,
            "longitude": -78.6336,
            "timezone": "America/New_York",
            "date": "2015-07-12",
            "calculation_method": "north_america",
            "madhab": "hanafi",
            "maghrib_adjustment": -3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["calculated_times"]["maghrib"] == "20:32"
    assert body["azan_times"]["maghrib"] == "20:29"


def test_isha_adjustment_can_roll_over_midnight() -> None:
    # A location/date where Isha is deliberately pushed past 23:59 to verify
    # the rollover is computed correctly rather than clipped or wrapped
    # incorrectly.
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 35.775,
            "longitude": -78.6336,
            "timezone": "America/New_York",
            "date": "2015-07-12",
            "calculation_method": "north_america",
            "madhab": "hanafi",
            "isha_adjustment": 150,
        },
    )

    assert response.status_code == 200

    body = response.json()

    # Calculated Isha is 21:57; +150 minutes = 00:27 the next calendar day.
    # The formatted HH:MM string reflects the rolled-over clock time.
    assert body["calculated_times"]["isha"] == "21:57"
    assert body["azan_times"]["isha"] == "00:27"


def test_adjustment_out_of_range_returns_422() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 25.2048,
            "longitude": 55.2708,
            "timezone": "Asia/Dubai",
            "date": "2026-09-14",
            "calculation_method": "dubai",
            "fajr_adjustment": 1441,
        },
    )

    assert response.status_code == 422


def test_invalid_calculation_method_returns_422() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 25.2048,
            "longitude": 55.2708,
            "timezone": "Asia/Dubai",
            "date": "2026-09-14",
            "calculation_method": "invalid_method",
        },
    )

    assert response.status_code == 422
