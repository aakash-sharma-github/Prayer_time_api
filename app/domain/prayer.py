from dataclasses import dataclass, fields
from datetime import date, datetime, timedelta
from enum import Enum
from zoneinfo import ZoneInfo


class CalculationMethodName(str, Enum):
    MUSLIM_WORLD_LEAGUE = "muslim_world_league"
    EGYPTIAN = "egyptian"
    KARACHI = "karachi"
    UMM_AL_QURA = "umm_al_qura"
    DUBAI = "dubai"
    IACAD_DUBAI = "iacad_dubai"
    MOON_SIGHTING_COMMITTEE = "moon_sighting_committee"
    NORTH_AMERICA = "north_america"
    KUWAIT = "kuwait"
    QATAR = "qatar"
    SINGAPORE = "singapore"
    UOIF = "uoif"


class MadhabName(str, Enum):
    SHAFI = "shafi"
    HANAFI = "hanafi"


class HighLatitudeRuleName(str, Enum):
    MIDDLE_OF_THE_NIGHT = "middle_of_the_night"
    SEVENTH_OF_THE_NIGHT = "seventh_of_the_night"
    TWILIGHT_ANGLE = "twilight_angle"


@dataclass(frozen=True)
class PrayerCalculationRequest:
    latitude: float
    longitude: float
    date: date
    timezone: ZoneInfo
    calculation_method: CalculationMethodName
    madhab: MadhabName = MadhabName.SHAFI
    high_latitude_rule: HighLatitudeRuleName = HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT


@dataclass(frozen=True)
class PrayerTimesResult:
    date: date
    timezone: ZoneInfo
    latitude: float
    longitude: float
    calculation_method: CalculationMethodName
    madhab: MadhabName
    high_latitude_rule: HighLatitudeRuleName
    fajr: datetime
    sunrise: datetime
    dhuhr: datetime
    asr: datetime
    sunset: datetime
    maghrib: datetime
    isha: datetime


@dataclass(frozen=True)
class PrayerAdjustments:
    """Caller-supplied Azan offsets in whole minutes.

    These offsets apply only to Fajr, Dhuhr, Asr, Maghrib, and Isha.
    Sunrise and sunset are astronomical events and are never adjusted.
    """

    fajr: int = 0
    dhuhr: int = 0
    asr: int = 0
    maghrib: int = 0
    isha: int = 0

    MINUTES_MIN = -1440
    MINUTES_MAX = 1440

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)

            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{field.name} adjustment must be an integer number of minutes")

            if not self.MINUTES_MIN <= value <= self.MINUTES_MAX:
                raise ValueError(
                    f"{field.name} adjustment must be between "
                    f"{self.MINUTES_MIN} and {self.MINUTES_MAX} minutes"
                )

    def apply(self, prayer_times: PrayerTimesResult) -> dict[str, datetime]:
        values = {
            "fajr": prayer_times.fajr,
            "dhuhr": prayer_times.dhuhr,
            "asr": prayer_times.asr,
            "maghrib": prayer_times.maghrib,
            "isha": prayer_times.isha,
        }
        adjustments = {field.name: getattr(self, field.name) for field in fields(self)}

        return {
            prayer_name: prayer_time + timedelta(minutes=adjustments[prayer_name])
            for prayer_name, prayer_time in values.items()
        }
