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

    assert body["times"] == {
        "fajr": "04:42",
        "sunrise": "06:08",
        "dhuhr": "13:21",
        "asr": "18:22",
        "sunset": "20:32",
        "maghrib": "20:32",
        "isha": "21:57",
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