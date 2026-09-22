from datetime import date as Date

from pydantic import BaseModel, ConfigDict, Field

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
)


class CoordinatesResponse(BaseModel):
    """The geographic coordinates used for the calculation."""

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


class CalculationMethodsResponse(BaseModel):
    """The calculation settings accepted by the v1 prayer-time endpoints."""

    calculation_methods: list[CalculationMethodName]
    madhabs: list[MadhabName]
    high_latitude_rules: list[HighLatitudeRuleName]


class PrayerTimesResponse(BaseModel):
    """The stable v1 response for a single location and calendar date."""

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

    date: Date = Field(description="Gregorian calculation date in the requested timezone.")
    timezone: str = Field(description="IANA timezone used for the calculation.")
    coordinates: CoordinatesResponse = Field(description="Coordinates used for the calculation.")
    calculation_method: CalculationMethodName = Field(
        description="Calculation method that was used."
    )
    madhab: MadhabName = Field(description="Madhab used for the Asr calculation.")
    high_latitude_rule: HighLatitudeRuleName = Field(
        description="High-latitude rule used for the calculation."
    )
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
