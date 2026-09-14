from datetime import date
from zoneinfo import ZoneInfo

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerAdjustments,
    PrayerCalculationRequest,
)
from app.services.prayer_adjustments import PrayerAdjustmentService
from app.services.prayer_calculator import PrayerCalculator


def make_request() -> PrayerCalculationRequest:
    return PrayerCalculationRequest(
        latitude=35.7750,
        longitude=-78.6336,
        date=date(2015, 7, 12),
        timezone=ZoneInfo("America/New_York"),
        calculation_method=CalculationMethodName.NORTH_AMERICA,
        madhab=MadhabName.HANAFI,
        high_latitude_rule=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
    )


def test_zero_adjustments_preserve_calculated_times() -> None:
    calculator = PrayerCalculator()
    service = PrayerAdjustmentService()
    result = calculator.calculate(make_request())
    adjusted = service.apply(result, PrayerAdjustments())
    assert adjusted["fajr"] == result.fajr
    assert adjusted["dhuhr"] == result.dhuhr
    assert adjusted["asr"] == result.asr
    assert adjusted["maghrib"] == result.maghrib
    assert adjusted["isha"] == result.isha


def test_positive_adjustments_are_applied_in_minutes() -> None:
    calculator = PrayerCalculator()
    service = PrayerAdjustmentService()
    result = calculator.calculate(make_request())
    adjusted = service.apply(
        result,
        PrayerAdjustments(fajr=2, dhuhr=1, asr=2, maghrib=1, isha=3),
    )
    assert adjusted["fajr"].strftime("%H:%M") == "04:44"
    assert adjusted["dhuhr"].strftime("%H:%M") == "13:22"
    assert adjusted["asr"].strftime("%H:%M") == "18:24"
    assert adjusted["maghrib"].strftime("%H:%M") == "20:33"
    assert adjusted["isha"].strftime("%H:%M") == "22:00"


def test_negative_adjustments_are_applied_in_minutes() -> None:
    calculator = PrayerCalculator()
    service = PrayerAdjustmentService()
    result = calculator.calculate(make_request())
    adjusted = service.apply(
        result,
        PrayerAdjustments(fajr=-2, dhuhr=-1, asr=-2, maghrib=-1, isha=-3),
    )
    assert adjusted["fajr"].strftime("%H:%M") == "04:40"
    assert adjusted["dhuhr"].strftime("%H:%M") == "13:20"
    assert adjusted["asr"].strftime("%H:%M") == "18:20"
    assert adjusted["maghrib"].strftime("%H:%M") == "20:31"
    assert adjusted["isha"].strftime("%H:%M") == "21:54"


def test_adjustments_do_not_include_sunrise_or_sunset() -> None:
    calculator = PrayerCalculator()
    service = PrayerAdjustmentService()
    result = calculator.calculate(make_request())
    adjusted = service.apply(
        result,
        PrayerAdjustments(fajr=10, dhuhr=10, asr=10, maghrib=10, isha=10),
    )
    assert set(adjusted) == {"fajr", "dhuhr", "asr", "maghrib", "isha"}
    assert result.sunrise.strftime("%H:%M") == "06:08"
    assert result.sunset.strftime("%H:%M") == "20:32"
