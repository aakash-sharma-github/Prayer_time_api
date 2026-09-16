from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Query

from app.api.errors import APIError
from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerAdjustments,
    PrayerCalculationRequest,
)
from app.schemas.errors import ErrorResponse, ValidationErrorResponse
from app.schemas.prayer import (
    AzanTimesResponse,
    CalculatedTimesResponse,
    CoordinatesResponse,
    PrayerAdjustmentsResponse,
    PrayerTimesResponse,
)
from app.services.prayer_adjustments import PrayerAdjustmentService
from app.services.prayer_calculator import PrayerCalculator

router = APIRouter(
    prefix="/api/v1",
    tags=["Prayer times"],
)

_calculator = PrayerCalculator()
_adjustment_service = PrayerAdjustmentService()


@router.get(
    "/prayer-times",
    response_model=PrayerTimesResponse,
    summary="Calculate prayer times and optional Azan adjustments",
    response_description=(
        "Prayer times in the requested timezone, with immutable calculated times and "
        "separately adjusted Azan times."
    ),
    description=(
        "Calculate astronomical prayer times for the requested coordinates and date. "
        "The calculated_times values are never modified by Azan adjustments. "
        "The five *_adjustment parameters add or subtract whole minutes from the "
        "corresponding Azan time only. Sunrise and sunset cannot be adjusted."
    ),
    responses={
        400: {
            "description": "The request is valid but cannot be calculated.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "INVALID_TIMEZONE",
                            "message": "Unknown IANA timezone: Not/ARealTimezone",
                        }
                    }
                }
            },
        },
        422: {
            "description": "One or more request parameters are invalid.",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Request validation failed.",
                            "details": [
                                {
                                    "field": "query.latitude",
                                    "message": "Input should be less than or equal to 90",
                                    "type": "less_than_equal",
                                }
                            ],
                        }
                    }
                }
            },
        },
    },
)
def get_prayer_times(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
        description="Decimal latitude from -90 to 90.",
        examples=[25.2048],
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
        description="Decimal longitude from -180 to 180.",
        examples=[55.2708],
    ),
    timezone: str = Query(
        ...,
        description="IANA timezone, for example Asia/Dubai.",
        examples=["Asia/Dubai"],
    ),
    date: date | None = Query(
        default=None,
        description="Gregorian date. Defaults to today in the requested timezone.",
        examples=["2026-09-14"],
    ),
    calculation_method: CalculationMethodName = Query(
        ...,
        description="Islamic prayer calculation method.",
        examples=["dubai"],
    ),
    madhab: MadhabName = Query(
        default=MadhabName.SHAFI,
        description="Madhab used for Asr calculation.",
    ),
    high_latitude_rule: HighLatitudeRuleName = Query(
        default=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
        description="Rule used when high-latitude adjustments are required.",
    ),
    fajr_adjustment: int = Query(
        default=0,
        ge=-1440,
        le=1440,
        description="Minutes added to Fajr Azan time. Sunrise is not adjustable.",
    ),
    dhuhr_adjustment: int = Query(
        default=0,
        ge=-1440,
        le=1440,
        description="Minutes added to Dhuhr Azan time.",
    ),
    asr_adjustment: int = Query(
        default=0,
        ge=-1440,
        le=1440,
        description="Minutes added to Asr Azan time.",
    ),
    maghrib_adjustment: int = Query(
        default=0,
        ge=-1440,
        le=1440,
        description="Minutes added to Maghrib Azan time.",
    ),
    isha_adjustment: int = Query(
        default=0,
        ge=-1440,
        le=1440,
        description="Minutes added to Isha Azan time.",
    ),
) -> PrayerTimesResponse:
    try:
        requested_timezone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise APIError(
            code="INVALID_TIMEZONE",
            message=f"Unknown IANA timezone: {timezone}",
            status_code=400,
        ) from exc

    requested_date = date or datetime.now(requested_timezone).date()

    request = PrayerCalculationRequest(
        latitude=latitude,
        longitude=longitude,
        date=requested_date,
        timezone=requested_timezone,
        calculation_method=calculation_method,
        madhab=madhab,
        high_latitude_rule=high_latitude_rule,
    )

    try:
        result = _calculator.calculate(request)
    except ValueError as exc:
        raise APIError(
            code="INVALID_CALCULATION",
            message=str(exc),
            status_code=400,
        ) from exc

    adjustments = PrayerAdjustments(
        fajr=fajr_adjustment,
        dhuhr=dhuhr_adjustment,
        asr=asr_adjustment,
        maghrib=maghrib_adjustment,
        isha=isha_adjustment,
    )
    azan_times = _adjustment_service.apply(result, adjustments)

    return PrayerTimesResponse(
        date=result.date,
        timezone=result.timezone.key,
        coordinates=CoordinatesResponse(
            latitude=result.latitude,
            longitude=result.longitude,
        ),
        calculation_method=result.calculation_method,
        madhab=result.madhab,
        high_latitude_rule=result.high_latitude_rule,
        calculated_times=CalculatedTimesResponse(
            fajr=result.fajr.strftime("%H:%M"),
            sunrise=result.sunrise.strftime("%H:%M"),
            dhuhr=result.dhuhr.strftime("%H:%M"),
            asr=result.asr.strftime("%H:%M"),
            sunset=result.sunset.strftime("%H:%M"),
            maghrib=result.maghrib.strftime("%H:%M"),
            isha=result.isha.strftime("%H:%M"),
        ),
        azan_times=AzanTimesResponse(
            fajr=azan_times["fajr"].strftime("%H:%M"),
            dhuhr=azan_times["dhuhr"].strftime("%H:%M"),
            asr=azan_times["asr"].strftime("%H:%M"),
            maghrib=azan_times["maghrib"].strftime("%H:%M"),
            isha=azan_times["isha"].strftime("%H:%M"),
        ),
        adjustments_minutes=PrayerAdjustmentsResponse(
            fajr=fajr_adjustment,
            dhuhr=dhuhr_adjustment,
            asr=asr_adjustment,
            maghrib=maghrib_adjustment,
            isha=isha_adjustment,
        ),
    )
