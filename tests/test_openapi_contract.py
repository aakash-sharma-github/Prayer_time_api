from app.main import app


def _parameter_by_name(operation: dict, name: str) -> dict:
    return next(parameter for parameter in operation["parameters"] if parameter["name"] == name)


def test_v1_prayer_times_openapi_contract_is_documented() -> None:
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/prayer-times"]["get"]

    assert operation["summary"] == "Calculate prayer times and optional Azan adjustments"
    assert operation["description"]
    assert operation["tags"] == ["Prayer times"]
    assert operation["responses"]["200"]["description"] == (
        "Prayer times in the requested timezone, with immutable calculated times and "
        "separately adjusted Azan times."
    )
    assert set(operation["responses"]) == {"200", "400", "422"}

    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}
    assert set(parameters) == {
        "latitude",
        "longitude",
        "timezone",
        "date",
        "calculation_method",
        "madhab",
        "high_latitude_rule",
        "fajr_adjustment",
        "dhuhr_adjustment",
        "asr_adjustment",
        "maghrib_adjustment",
        "isha_adjustment",
    }

    assert _parameter_by_name(operation, "latitude")["schema"] == {
        "type": "number",
        "maximum": 90,
        "minimum": -90,
        "title": "Latitude",
        "description": "Decimal latitude from -90 to 90.",
        "examples": [25.2048],
    }
    assert _parameter_by_name(operation, "longitude")["schema"]["minimum"] == -180
    assert _parameter_by_name(operation, "longitude")["schema"]["maximum"] == 180
    assert _parameter_by_name(operation, "madhab")["schema"]["default"] == "shafi"
    assert (
        _parameter_by_name(operation, "high_latitude_rule")["schema"]["default"]
        == "middle_of_the_night"
    )

    for name in (
        "fajr_adjustment",
        "dhuhr_adjustment",
        "asr_adjustment",
        "maghrib_adjustment",
        "isha_adjustment",
    ):
        parameter_schema = parameters[name]["schema"]
        assert parameter_schema["default"] == 0
        assert parameter_schema["minimum"] == -1440
        assert parameter_schema["maximum"] == 1440


def test_v1_openapi_documents_success_and_error_schemas_and_examples() -> None:
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/prayer-times"]["get"]
    responses = operation["responses"]

    assert responses["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/PrayerTimesResponse"
    }
    assert responses["400"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }
    assert responses["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ValidationErrorResponse"
    }
    assert responses["400"]["content"]["application/json"]["example"]["error"]["code"] == (
        "INVALID_TIMEZONE"
    )
    assert responses["422"]["content"]["application/json"]["example"]["error"]["code"] == (
        "VALIDATION_ERROR"
    )

    components = schema["components"]["schemas"]
    assert components["CalculationMethodName"]["enum"] == [
        "muslim_world_league",
        "egyptian",
        "karachi",
        "umm_al_qura",
        "dubai",
        "iacad_dubai",
        "moon_sighting_committee",
        "north_america",
        "kuwait",
        "qatar",
        "singapore",
        "uoif",
    ]
    assert components["MadhabName"]["enum"] == ["shafi", "hanafi"]
    assert components["HighLatitudeRuleName"]["enum"] == [
        "middle_of_the_night",
        "seventh_of_the_night",
        "twilight_angle",
    ]
    assert components["PrayerTimesResponse"]["example"]["azan_times"]["isha"] == "21:57"
    assert components["ErrorResponse"]["example"]["error"]["code"] == "INVALID_TIMEZONE"
    assert components["ValidationErrorResponse"]["example"]["error"]["details"]


def test_v1_range_openapi_contract_is_documented() -> None:
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/prayer-times/range"]["get"]
    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}

    assert operation["summary"] == "Calculate prayer times for an inclusive date range"
    assert operation["tags"] == ["Prayer times"]
    assert set(operation["responses"]) == {"200", "400", "422"}
    assert set(parameters) == {
        "latitude",
        "longitude",
        "timezone",
        "start_date",
        "end_date",
        "calculation_method",
        "madhab",
        "high_latitude_rule",
        "fajr_adjustment",
        "dhuhr_adjustment",
        "asr_adjustment",
        "maghrib_adjustment",
        "isha_adjustment",
    }
    assert parameters["start_date"]["required"] is True
    assert parameters["end_date"]["required"] is True
    assert parameters["latitude"]["schema"]["minimum"] == -90
    assert parameters["latitude"]["schema"]["maximum"] == 90

    for name in (
        "fajr_adjustment",
        "dhuhr_adjustment",
        "asr_adjustment",
        "maghrib_adjustment",
        "isha_adjustment",
    ):
        assert parameters[name]["schema"]["default"] == 0
        assert parameters[name]["schema"]["minimum"] == -1440
        assert parameters[name]["schema"]["maximum"] == 1440

    responses = operation["responses"]
    assert responses["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/PrayerTimesRangeResponse"
    }
    examples = responses["400"]["content"]["application/json"]["examples"]
    assert examples["invalid_date_range"]["value"]["error"]["code"] == "INVALID_DATE_RANGE"
    assert examples["date_range_too_large"]["value"]["error"]["code"] == "DATE_RANGE_TOO_LARGE"
