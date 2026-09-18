from copy import copy
from datetime import datetime, time, timezone

from adhanpy.calculation.CalculationMethod import CalculationMethod
from adhanpy.calculation.CalculationParameters import CalculationParameters
from adhanpy.calculation.HighLatitudeRule import HighLatitudeRule
from adhanpy.calculation.Madhab import Madhab
from adhanpy.PrayerTimes import (
    Coordinates,
    DateComponents,
    PrayerTimes,
    SolarTime,
    TimeComponents,
)

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerCalculationRequest,
    PrayerTimesResult,
)

_CALCULATION_METHODS = {
    CalculationMethodName.MUSLIM_WORLD_LEAGUE: CalculationMethod.MUSLIM_WORLD_LEAGUE,
    CalculationMethodName.EGYPTIAN: CalculationMethod.EGYPTIAN,
    CalculationMethodName.KARACHI: CalculationMethod.KARACHI,
    CalculationMethodName.UMM_AL_QURA: CalculationMethod.UMM_AL_QURA,
    CalculationMethodName.DUBAI: CalculationMethod.DUBAI,
    CalculationMethodName.IACAD_DUBAI: CalculationMethod.DUBAI,
    CalculationMethodName.MOON_SIGHTING_COMMITTEE: (CalculationMethod.MOON_SIGHTING_COMMITTEE),
    CalculationMethodName.NORTH_AMERICA: CalculationMethod.NORTH_AMERICA,
    CalculationMethodName.KUWAIT: CalculationMethod.KUWAIT,
    CalculationMethodName.QATAR: CalculationMethod.QATAR,
    CalculationMethodName.SINGAPORE: CalculationMethod.SINGAPORE,
    CalculationMethodName.UOIF: CalculationMethod.UOIF,
}

_MADHABS = {
    MadhabName.SHAFI: Madhab.SHAFI,
    MadhabName.HANAFI: Madhab.HANAFI,
}

_HIGH_LATITUDE_RULES = {
    HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT: (HighLatitudeRule.MIDDLE_OF_THE_NIGHT),
    HighLatitudeRuleName.SEVENTH_OF_THE_NIGHT: (HighLatitudeRule.SEVENTH_OF_THE_NIGHT),
    HighLatitudeRuleName.TWILIGHT_ANGLE: HighLatitudeRule.TWILIGHT_ANGLE,
}


class PrayerCalculator:
    """Application adapter around the adhanpy calculation engine."""

    def calculate(self, request: PrayerCalculationRequest) -> PrayerTimesResult:
        self._validate_coordinates(request.latitude, request.longitude)

        calculation_method = _CALCULATION_METHODS[request.calculation_method]

        parameters = CalculationParameters(method=calculation_method)
        parameters.madhab = _MADHABS[request.madhab]
        parameters.high_latitude_rule = _HIGH_LATITUDE_RULES[request.high_latitude_rule]
        if request.calculation_method == CalculationMethodName.IACAD_DUBAI:
            # Keep adhanpy's Dubai astronomical profile while applying the IACAD-
            # validated internal Asr method offset. This is deliberately separate
            # from caller-controlled Azan adjustments. adhanpy reuses the method
            # adjustment object, so copy it before changing this calculation only.
            parameters.method_adjustments = copy(parameters.method_adjustments)
            parameters.method_adjustments.asr = 1

        # adhanpy converts the supplied date through UTC internally.
        # UTC noon prevents a positive-offset timezone from rolling the
        # requested calendar date back to the previous UTC date.
        calculation_date = datetime.combine(
            request.date,
            time(hour=12),
            tzinfo=timezone.utc,
        )

        prayer_times = PrayerTimes(
            (request.latitude, request.longitude),
            calculation_date,
            calculation_parameters=parameters,
            time_zone=request.timezone,
        )

        sunset = self._calculate_sunset(
            request.latitude,
            request.longitude,
            request.date,
            request.timezone,
        )

        return PrayerTimesResult(
            date=request.date,
            timezone=request.timezone,
            latitude=request.latitude,
            longitude=request.longitude,
            calculation_method=request.calculation_method,
            madhab=request.madhab,
            high_latitude_rule=request.high_latitude_rule,
            fajr=prayer_times.fajr,
            sunrise=prayer_times.sunrise,
            dhuhr=prayer_times.dhuhr,
            asr=prayer_times.asr,
            sunset=sunset,
            maghrib=prayer_times.maghrib,
            isha=prayer_times.isha,
        )

    @staticmethod
    def _calculate_sunset(
        latitude: float,
        longitude: float,
        requested_date,
        requested_timezone,
    ):
        date_components = DateComponents(
            requested_date.year,
            requested_date.month,
            requested_date.day,
        )

        coordinates = Coordinates(latitude, longitude)

        solar_time = SolarTime(
            date_components,
            coordinates,
        )

        sunset_components = TimeComponents.from_float(solar_time.sunset)

        if sunset_components is None:
            raise RuntimeError("Unable to calculate sunset.")

        sunset_utc = sunset_components.date_components(date_components)

        return sunset_utc.astimezone(requested_timezone)

    @staticmethod
    def _validate_coordinates(latitude: float, longitude: float) -> None:
        if not -90.0 <= latitude <= 90.0:
            raise ValueError("Latitude must be between -90 and 90.")

        if not -180.0 <= longitude <= 180.0:
            raise ValueError("Longitude must be between -180 and 180.")
