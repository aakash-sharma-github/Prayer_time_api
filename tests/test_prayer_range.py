from datetime import date, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.api.errors import APIError
from app.api.v1.prayer_times_range import get_prayer_times_range
from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerAdjustments,
)
from app.services.prayer_range import (
    MAX_RANGE_DAYS,
    DateRangeTooLargeError,
    InvalidDateRangeError,
    PrayerRangeService,
)

RANGE_OPTIONS = {
    "latitude": 25.2048,
    "longitude": 55.2708,
    "timezone": "Asia/Dubai",
    "calculation_method": CalculationMethodName.DUBAI,
    "madhab": MadhabName.SHAFI,
    "high_latitude_rule": HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
    "fajr_adjustment": 0,
    "dhuhr_adjustment": 0,
    "asr_adjustment": 0,
    "maghrib_adjustment": 0,
    "isha_adjustment": 0,
}


def test_range_endpoint_returns_one_inclusive_day() -> None:
    response = get_prayer_times_range(
        **RANGE_OPTIONS,
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 15),
    )

    assert response.start_date == date(2026, 9, 15)
    assert response.end_date == date(2026, 9, 15)
    assert [day.date for day in response.days] == [date(2026, 9, 15)]


def test_range_endpoint_is_inclusive_and_chronological() -> None:
    response = get_prayer_times_range(
        **{**RANGE_OPTIONS, "fajr_adjustment": 2, "isha_adjustment": 10},
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 17),
    )

    assert [day.date for day in response.days] == [
        date(2026, 9, 15),
        date(2026, 9, 16),
        date(2026, 9, 17),
    ]
    assert response.adjustments_minutes.model_dump() == {
        "fajr": 2,
        "dhuhr": 0,
        "asr": 0,
        "maghrib": 0,
        "isha": 10,
    }
    for day in response.days:
        assert day.calculated_times.fajr != day.azan_times.fajr
        assert day.calculated_times.isha != day.azan_times.isha
        assert day.calculated_times.dhuhr == day.azan_times.dhuhr
        assert day.calculated_times.asr == day.azan_times.asr
        assert day.calculated_times.maghrib == day.azan_times.maghrib
        assert "sunrise" not in day.azan_times.model_dump()
        assert "sunset" not in day.azan_times.model_dump()


def test_range_calculates_each_date_independently() -> None:
    service = PrayerRangeService()
    timezone = ZoneInfo("Asia/Dubai")
    days = service.calculate(
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 16),
        latitude=25.2048,
        longitude=55.2708,
        timezone=timezone,
        calculation_method=CalculationMethodName.DUBAI,
        madhab=MadhabName.SHAFI,
        high_latitude_rule=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
        adjustments=PrayerAdjustments(),
    )

    assert [day.result.date for day in days] == [date(2026, 9, 15), date(2026, 9, 16)]
    assert all(day.result.timezone == timezone for day in days)


def test_range_supports_iacad_dubai_with_its_internal_asr_offset() -> None:
    service = PrayerRangeService()
    days = service.calculate(
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 16),
        latitude=25.2048,
        longitude=55.2708,
        timezone=ZoneInfo("Asia/Dubai"),
        calculation_method=CalculationMethodName.IACAD_DUBAI,
        madhab=MadhabName.SHAFI,
        high_latitude_rule=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
        adjustments=PrayerAdjustments(asr=2),
    )

    assert [day.result.asr.strftime("%H:%M") for day in days] == ["15:42", "15:42"]
    assert [day.azan_times["asr"].strftime("%H:%M") for day in days] == ["15:44", "15:44"]


def test_range_supports_all_calculation_methods_and_high_latitude_rules() -> None:
    service = PrayerRangeService()
    for calculation_method in CalculationMethodName:
        for high_latitude_rule in HighLatitudeRuleName:
            days = service.calculate(
                start_date=date(2026, 9, 15),
                end_date=date(2026, 9, 15),
                latitude=25.2048,
                longitude=55.2708,
                timezone=ZoneInfo("Asia/Dubai"),
                calculation_method=calculation_method,
                madhab=MadhabName.SHAFI,
                high_latitude_rule=high_latitude_rule,
                adjustments=PrayerAdjustments(),
            )
            assert len(days) == 1


def test_range_supports_both_madhabs() -> None:
    service = PrayerRangeService()
    asr_times = []
    for madhab in MadhabName:
        result = service.calculate(
            start_date=date(2026, 9, 15),
            end_date=date(2026, 9, 15),
            latitude=25.2048,
            longitude=55.2708,
            timezone=ZoneInfo("Asia/Dubai"),
            calculation_method=CalculationMethodName.DUBAI,
            madhab=madhab,
            high_latitude_rule=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
            adjustments=PrayerAdjustments(),
        )[0]
        asr_times.append(result.result.asr)

    assert asr_times[0] != asr_times[1]


def test_range_adjustments_apply_to_every_date_and_preserve_calculated_times() -> None:
    service = PrayerRangeService()
    adjustments = PrayerAdjustments(fajr=1, dhuhr=-2, asr=3, maghrib=-4, isha=150)
    days = service.calculate(
        start_date=date(2015, 7, 12),
        end_date=date(2015, 7, 13),
        latitude=35.775,
        longitude=-78.6336,
        timezone=ZoneInfo("America/New_York"),
        calculation_method=CalculationMethodName.NORTH_AMERICA,
        madhab=MadhabName.HANAFI,
        high_latitude_rule=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
        adjustments=adjustments,
    )

    for day in days:
        assert day.azan_times["fajr"] == day.result.fajr + timedelta(minutes=1)
        assert day.azan_times["dhuhr"] == day.result.dhuhr - timedelta(minutes=2)
        assert day.azan_times["asr"] == day.result.asr + timedelta(minutes=3)
        assert day.azan_times["maghrib"] == day.result.maghrib - timedelta(minutes=4)
        assert day.azan_times["isha"] == day.result.isha + timedelta(minutes=150)
        assert day.result.sunrise.strftime("%H:%M")
        assert day.result.sunset.strftime("%H:%M")


def test_range_rejects_reversed_dates_and_excessive_ranges() -> None:
    service = PrayerRangeService()
    options = {
        "latitude": 25.2048,
        "longitude": 55.2708,
        "timezone": ZoneInfo("Asia/Dubai"),
        "calculation_method": CalculationMethodName.DUBAI,
        "madhab": MadhabName.SHAFI,
        "high_latitude_rule": HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
        "adjustments": PrayerAdjustments(),
    }

    with pytest.raises(InvalidDateRangeError, match="start_date must be on or before end_date"):
        service.calculate(
            **options,
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 15),
        )

    with pytest.raises(DateRangeTooLargeError, match="Date range cannot exceed 366 days"):
        service.calculate(
            **options,
            start_date=date(2026, 1, 1),
            end_date=date(2027, 1, 2),
        )


def test_range_allows_exactly_366_dates() -> None:
    service = PrayerRangeService()
    days = service.calculate(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        latitude=25.2048,
        longitude=55.2708,
        timezone=ZoneInfo("Asia/Dubai"),
        calculation_method=CalculationMethodName.DUBAI,
        madhab=MadhabName.SHAFI,
        high_latitude_rule=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
        adjustments=PrayerAdjustments(),
    )

    assert len(days) == MAX_RANGE_DAYS


def test_range_endpoint_uses_standardized_range_errors() -> None:
    with pytest.raises(APIError) as error:
        get_prayer_times_range(
            **RANGE_OPTIONS,
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 15),
        )

    assert error.value.code == "INVALID_DATE_RANGE"
    assert error.value.message == "start_date must be on or before end_date"

    with pytest.raises(APIError) as error:
        get_prayer_times_range(
            **RANGE_OPTIONS,
            start_date=date(2026, 1, 1),
            end_date=date(2027, 1, 2),
        )

    assert error.value.code == "DATE_RANGE_TOO_LARGE"
    assert error.value.message == "Date range cannot exceed 366 days"

    with pytest.raises(APIError) as error:
        get_prayer_times_range(
            **{**RANGE_OPTIONS, "timezone": "Not/ARealTimezone"},
            start_date=date(2026, 9, 15),
            end_date=date(2026, 9, 15),
        )

    assert error.value.code == "INVALID_TIMEZONE"
