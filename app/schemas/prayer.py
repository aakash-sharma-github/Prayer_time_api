from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
)


class CoordinatesResponse(BaseModel):
    latitude: float
    longitude: float


class CalculatedTimesResponse(BaseModel):
    """Astronomically calculated prayer and solar-event times."""

    fajr: str
    sunrise: str
    dhuhr: str
    asr: str
    sunset: str
    maghrib: str
    isha: str


class AzanTimesResponse(BaseModel):
    """Final Azan times after caller-supplied minute adjustments."""

    fajr: str
    dhuhr: str
    asr: str
    maghrib: str
    isha: str


class PrayerAdjustmentsResponse(BaseModel):
    """Explicit Azan offsets supplied by the caller, in minutes."""

    fajr: int = Field(ge=-1440, le=1440)
    dhuhr: int = Field(ge=-1440, le=1440)
    asr: int = Field(ge=-1440, le=1440)
    maghrib: int = Field(ge=-1440, le=1440)
    isha: int = Field(ge=-1440, le=1440)


class PrayerTimesResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2015-07-12",
                "timezone": "America/New_York",
                "coordinates": {
                    "latitude": 35.775,
                    "longitude": -78.6336,
                },
                "calculation_method": "north_america",
                "madhab": "hanafi",
                "high_latitude_rule": "middle_of_the_night",
                "calculated_times": {
                    "fajr": "04:42",
                    "sunrise": "06:08",
                    "dhuhr": "13:21",
                    "asr": "18:22",
                    "sunset": "20:32",
                    "maghrib": "20:32",
                    "isha": "21:57",
                },
                "azan_times": {
                    "fajr": "04:42",
                    "dhuhr": "13:21",
                    "asr": "18:22",
                    "maghrib": "20:32",
                    "isha": "21:57",
                },
                "adjustments_minutes": {
                    "fajr": 0,
                    "dhuhr": 0,
                    "asr": 0,
                    "maghrib": 0,
                    "isha": 0,
                },
            }
        }
    )

    date: date
    timezone: str
    coordinates: CoordinatesResponse
    calculation_method: CalculationMethodName
    madhab: MadhabName
    high_latitude_rule: HighLatitudeRuleName
    calculated_times: CalculatedTimesResponse = Field(
        description=(
            "Prayer and solar-event times calculated by the astronomical engine. "
            "These values are not changed by Azan adjustments."
        )
    )
    azan_times: AzanTimesResponse = Field(
        description=(
            "Final Azan times after the caller's per-prayer minute adjustments. "
            "Sunrise and sunset are excluded because they are not Azan prayers."
        )
    )
    adjustments_minutes: PrayerAdjustmentsResponse = Field(
        description=(
            "Per-prayer Azan adjustments in minutes. "
            "Allowed prayers: Fajr, Dhuhr, Asr, Maghrib, and Isha. "
            "Sunrise and sunset cannot be adjusted. Range: -1440 to 1440."
        )
    )
