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
                "times": {
                    "fajr": "04:42",
                    "sunrise": "06:08",
                    "dhuhr": "13:21",
                    "asr": "18:22",
                    "sunset": "20:32",
                    "maghrib": "20:32",
                    "isha": "21:57",
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

    times: dict[str, str] = Field(description="Prayer times formatted as local HH:MM values.")
