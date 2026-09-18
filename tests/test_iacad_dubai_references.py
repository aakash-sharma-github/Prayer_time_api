import csv
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerCalculationRequest,
)
from app.services.prayer_calculator import PrayerCalculator

_REFERENCE_PATH = Path(__file__).parent / "fixtures" / "iacad_dubai_ramadan_2026.csv"
_PRAYERS = ("fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha")


def _references() -> list[dict[str, str]]:
    with _REFERENCE_PATH.open(newline="") as file:
        return list(csv.DictReader(file))


def _minutes(value: str) -> int:
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


@pytest.mark.parametrize("reference", _references(), ids=lambda row: row["date"])
def test_iacad_dubai_matches_official_ramadan_2026_references_within_one_minute(
    reference: dict[str, str],
) -> None:
    """IACAD Dubai calendar: 18 February–19 March 2026; see fixtures/README.md."""
    result = PrayerCalculator().calculate(
        PrayerCalculationRequest(
            latitude=25.2048,
            longitude=55.27055,
            date=date.fromisoformat(reference["date"]),
            timezone=ZoneInfo("Asia/Dubai"),
            calculation_method=CalculationMethodName.IACAD_DUBAI,
            madhab=MadhabName.SHAFI,
            high_latitude_rule=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
        )
    )

    for prayer_name in _PRAYERS:
        calculated = getattr(result, prayer_name).strftime("%H:%M")
        assert abs(_minutes(calculated) - _minutes(reference[prayer_name])) <= 1
