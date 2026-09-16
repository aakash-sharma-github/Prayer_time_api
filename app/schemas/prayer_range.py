from datetime import date as Date

from pydantic import BaseModel, ConfigDict, Field

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
)
from app.schemas.prayer import (
    AzanTimesResponse,
    CalculatedTimesResponse,
    CoordinatesResponse,
    PrayerAdjustmentsResponse,
)


class PrayerTimesRangeDayResponse(BaseModel):
    """Prayer times for one local date within a range response."""

    date: Date = Field(description="Gregorian calculation date in the requested timezone.")
    calculated_times: CalculatedTimesResponse
    azan_times: AzanTimesResponse


class PrayerTimesRangeResponse(BaseModel):
    """Stable v1 response for an inclusive range of local calendar dates."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2026-09-15",
                "end_date": "2026-09-17",
                "timezone": "Asia/Dubai",
                "coordinates": {"latitude": 25.2048, "longitude": 55.2708},
                "calculation_method": "dubai",
                "madhab": "shafi",
                "high_latitude_rule": "middle_of_the_night",
                "adjustments_minutes": {
                    "fajr": 0,
                    "dhuhr": 0,
                    "asr": 0,
                    "maghrib": 0,
                    "isha": 0,
                },
                "days": [
                    {
                        "date": "2026-09-15",
                        "calculated_times": {
                            "fajr": "04:47",
                            "sunrise": "06:01",
                            "dhuhr": "12:17",
                            "asr": "15:43",
                            "sunset": "18:22",
                            "maghrib": "18:25",
                            "isha": "19:39",
                        },
                        "azan_times": {
                            "fajr": "04:47",
                            "dhuhr": "12:17",
                            "asr": "15:43",
                            "maghrib": "18:25",
                            "isha": "19:39",
                        },
                    }
                ],
            }
        }
    )

    start_date: Date
    end_date: Date
    timezone: str
    coordinates: CoordinatesResponse
    calculation_method: CalculationMethodName
    madhab: MadhabName
    high_latitude_rule: HighLatitudeRuleName
    adjustments_minutes: PrayerAdjustmentsResponse
    days: list[PrayerTimesRangeDayResponse] = Field(
        description=(
            "Independently calculated days in chronological order, inclusive of both bounds."
        )
    )
