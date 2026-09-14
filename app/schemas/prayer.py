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
    fajr: str
    sunrise: str
    dhuhr: str
    asr: str
    sunset: str
    maghrib: str
    isha: str


class AzanTimesResponse(BaseModel):
    fajr: str
    dhuhr: str
    asr: str
    maghrib: str
    isha: str


class PrayerAdjustmentsResponse(BaseModel):
    fajr: int
    dhuhr: int
    asr: int
    maghrib: int
    isha: int


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
    calculated_times: CalculatedTimesResponse
    azan_times: AzanTimesResponse
    adjustments_minutes: PrayerAdjustmentsResponse = Field(
        description="Per-prayer Azan adjustments in minutes."
    )
