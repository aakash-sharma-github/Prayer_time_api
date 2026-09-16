from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerAdjustments,
    PrayerCalculationRequest,
    PrayerTimesResult,
)
from app.services.prayer_adjustments import PrayerAdjustmentService
from app.services.prayer_calculator import PrayerCalculator

MAX_RANGE_DAYS = 366


class InvalidDateRangeError(ValueError):
    """Raised when a range ends before it starts."""


class DateRangeTooLargeError(ValueError):
    """Raised when an inclusive range contains too many dates."""


@dataclass(frozen=True)
class PrayerTimesRangeDay:
    """Calculated and adjusted times for one requested local calendar date."""

    result: PrayerTimesResult
    azan_times: dict[str, datetime]


class PrayerRangeService:
    """Calculate independently computed prayer times for an inclusive date range."""

    def __init__(
        self,
        calculator: PrayerCalculator | None = None,
        adjustment_service: PrayerAdjustmentService | None = None,
    ) -> None:
        self._calculator = calculator or PrayerCalculator()
        self._adjustment_service = adjustment_service or PrayerAdjustmentService()

    def calculate(
        self,
        *,
        start_date: date,
        end_date: date,
        latitude: float,
        longitude: float,
        timezone: ZoneInfo,
        calculation_method: CalculationMethodName,
        madhab: MadhabName,
        high_latitude_rule: HighLatitudeRuleName,
        adjustments: PrayerAdjustments,
    ) -> list[PrayerTimesRangeDay]:
        number_of_days = (end_date - start_date).days + 1
        if number_of_days < 1:
            raise InvalidDateRangeError("start_date must be on or before end_date")
        if number_of_days > MAX_RANGE_DAYS:
            raise DateRangeTooLargeError(f"Date range cannot exceed {MAX_RANGE_DAYS} days")

        days: list[PrayerTimesRangeDay] = []
        for offset in range(number_of_days):
            requested_date = start_date + timedelta(days=offset)
            result = self._calculator.calculate(
                PrayerCalculationRequest(
                    latitude=latitude,
                    longitude=longitude,
                    date=requested_date,
                    timezone=timezone,
                    calculation_method=calculation_method,
                    madhab=madhab,
                    high_latitude_rule=high_latitude_rule,
                )
            )
            days.append(
                PrayerTimesRangeDay(
                    result=result,
                    azan_times=self._adjustment_service.apply(result, adjustments),
                )
            )

        return days
