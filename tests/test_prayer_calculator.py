from datetime import date
from zoneinfo import ZoneInfo

import pytest

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerCalculationRequest,
)
from app.services.prayer_calculator import PrayerCalculator


def make_request(
    *,
    latitude: float = 35.7750,
    longitude: float = -78.6336,
    calculation_method: CalculationMethodName = (CalculationMethodName.NORTH_AMERICA),
    madhab: MadhabName = MadhabName.HANAFI,
    high_latitude_rule: HighLatitudeRuleName = (HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT),
) -> PrayerCalculationRequest:
    return PrayerCalculationRequest(
        latitude=latitude,
        longitude=longitude,
        date=date(2015, 7, 12),
        timezone=ZoneInfo("America/New_York"),
        calculation_method=calculation_method,
        madhab=madhab,
        high_latitude_rule=high_latitude_rule,
    )


def test_north_america_hanafi_reference_case() -> None:
    calculator = PrayerCalculator()

    result = calculator.calculate(make_request())

    assert result.fajr.strftime("%H:%M") == "04:42"
    assert result.sunrise.strftime("%H:%M") == "06:08"
    assert result.dhuhr.strftime("%H:%M") == "13:21"
    assert result.asr.strftime("%H:%M") == "18:22"
    assert result.maghrib.strftime("%H:%M") == "20:32"
    assert result.isha.strftime("%H:%M") == "21:57"


def test_madhab_changes_asr_time() -> None:
    calculator = PrayerCalculator()

    shafi_result = calculator.calculate(make_request(madhab=MadhabName.SHAFI))
    hanafi_result = calculator.calculate(make_request(madhab=MadhabName.HANAFI))

    assert shafi_result.asr.strftime("%H:%M") == "17:09"
    assert hanafi_result.asr.strftime("%H:%M") == "18:22"


def test_all_times_are_timezone_aware() -> None:
    calculator = PrayerCalculator()

    result = calculator.calculate(make_request())

    times = (
        result.fajr,
        result.sunrise,
        result.dhuhr,
        result.asr,
        result.sunset,
        result.maghrib,
        result.isha,
    )

    for prayer_time in times:
        assert prayer_time.tzinfo is not None
        assert prayer_time.utcoffset() is not None
        assert prayer_time.tzinfo.key == "America/New_York"


def test_invalid_latitude_is_rejected() -> None:
    calculator = PrayerCalculator()

    request = make_request(latitude=91.0)

    with pytest.raises(ValueError, match="Latitude"):
        calculator.calculate(request)


def test_invalid_longitude_is_rejected() -> None:
    calculator = PrayerCalculator()

    request = make_request(longitude=181.0)

    with pytest.raises(ValueError, match="Longitude"):
        calculator.calculate(request)


def test_positive_timezone_preserves_requested_date() -> None:
    calculator = PrayerCalculator()

    request = PrayerCalculationRequest(
        latitude=25.2048,
        longitude=55.2708,
        date=date(2026, 9, 14),
        timezone=ZoneInfo("Asia/Dubai"),
        calculation_method=CalculationMethodName.DUBAI,
        madhab=MadhabName.SHAFI,
        high_latitude_rule=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
    )

    result = calculator.calculate(request)

    assert result.fajr.date() == date(2026, 9, 14)
    assert result.sunrise.date() == date(2026, 9, 14)
    assert result.dhuhr.date() == date(2026, 9, 14)
    assert result.asr.date() == date(2026, 9, 14)
    assert result.sunset.date() == date(2026, 9, 14)
    assert result.maghrib.date() == date(2026, 9, 14)
    assert result.isha.date() == date(2026, 9, 14)
