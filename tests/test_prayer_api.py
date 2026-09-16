from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def assert_validation_error(
    response,
    *,
    field: str,
    error_type: str,
) -> None:
    assert response.status_code == 422

    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed."
    assert len(body["error"]["details"]) == 1

    detail = body["error"]["details"][0]
    assert detail["field"] == field
    assert detail["type"] == error_type
    assert detail["message"]


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


def test_dubai_baseline_and_positive_adjustment() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 25.2048,
            "longitude": 55.2708,
            "timezone": "Asia/Dubai",
            "date": "2026-09-15",
            "calculation_method": "dubai",
            "madhab": "shafi",
            "fajr_adjustment": 2,
            "isha_adjustment": 10,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["date"] == "2026-09-15"
    assert body["calculated_times"] == {
        "fajr": "04:47",
        "sunrise": "06:02",
        "dhuhr": "12:17",
        "asr": "15:44",
        "sunset": "18:23",
        "maghrib": "18:26",
        "isha": "19:41",
    }
    assert body["azan_times"] == {
        "fajr": "04:49",
        "dhuhr": "12:17",
        "asr": "15:44",
        "maghrib": "18:26",
        "isha": "19:51",
    }
    assert body["adjustments_minutes"] == {
        "fajr": 2,
        "dhuhr": 0,
        "asr": 0,
        "maghrib": 0,
        "isha": 10,
    }


def test_dubai_negative_adjustment() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 25.2048,
            "longitude": 55.2708,
            "timezone": "Asia/Dubai",
            "date": "2026-09-15",
            "calculation_method": "dubai",
            "maghrib_adjustment": -3,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["calculated_times"]["maghrib"] == "18:26"
    assert body["azan_times"]["maghrib"] == "18:23"


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
    assert response.json()["date"] == "2026-09-14"


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
    assert response.json() == {
        "error": {
            "code": "INVALID_TIMEZONE",
            "message": "Unknown IANA timezone: Not/ARealTimezone",
        }
    }


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

    assert_validation_error(
        response,
        field="query.latitude",
        error_type="less_than_equal",
    )


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

    assert body["calculated_times"]["fajr"] == "04:42"
    assert body["calculated_times"]["isha"] == "21:57"
    assert body["azan_times"]["fajr"] == "04:47"
    assert body["azan_times"]["isha"] == "22:07"

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

    assert_validation_error(
        response,
        field="query.fajr_adjustment",
        error_type="less_than_equal",
    )


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

    assert_validation_error(
        response,
        field="query.calculation_method",
        error_type="enum",
    )


def test_invalid_madhab_returns_422() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 25.2048,
            "longitude": 55.2708,
            "timezone": "Asia/Dubai",
            "date": "2026-09-14",
            "calculation_method": "dubai",
            "madhab": "invalid_madhab",
        },
    )

    assert response.status_code == 422


def test_invalid_high_latitude_rule_returns_422() -> None:
    response = client.get(
        "/api/v1/prayer-times",
        params={
            "latitude": 25.2048,
            "longitude": 55.2708,
            "timezone": "Asia/Dubai",
            "date": "2026-09-14",
            "calculation_method": "dubai",
            "high_latitude_rule": "invalid_rule",
        },
    )

    assert response.status_code == 422


def test_all_adjustment_parameters_are_validated() -> None:
    for parameter in (
        "fajr_adjustment",
        "dhuhr_adjustment",
        "asr_adjustment",
        "maghrib_adjustment",
        "isha_adjustment",
    ):
        response = client.get(
            "/api/v1/prayer-times",
            params={
                "latitude": 25.2048,
                "longitude": 55.2708,
                "timezone": "Asia/Dubai",
                "date": "2026-09-14",
                "calculation_method": "dubai",
                parameter: 1441,
            },
        )
        assert response.status_code == 422
