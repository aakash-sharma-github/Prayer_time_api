from datetime import date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Query

from app.api.errors import APIError
from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerAdjustments,
)
from app.schemas.errors import ErrorResponse, ValidationErrorResponse
from app.schemas.prayer import (
    AzanTimesResponse,
    CalculatedTimesResponse,
    CoordinatesResponse,
    PrayerAdjustmentsResponse,
)
from app.schemas.prayer_range import PrayerTimesRangeDayResponse, PrayerTimesRangeResponse
from app.services.prayer_range import (
    DateRangeTooLargeError,
    InvalidDateRangeError,
    PrayerRangeService,
)

router = APIRouter(prefix="/api/v1", tags=["Prayer times"])

_range_service = PrayerRangeService()


@router.get(
    "/prayer-times/range",
    response_model=PrayerTimesRangeResponse,
    summary="Calculate prayer times for an inclusive date range",
    response_description=(
        "Prayer times in chronological order for each requested local date, with immutable "
        "calculated times and separately adjusted Azan times."
    ),
    description=(
        "Calculate each requested local calendar date independently using the existing prayer "
        "calculation engine. The range is inclusive and limited to 366 dates. Azan adjustments "
        "apply identically to every day and never modify calculated_times."
    ),
    responses={
        400: {
            "description": "The request is valid but cannot be calculated.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_date_range": {
                            "summary": "End date precedes start date",
                            "value": {
                                "error": {
                                    "code": "INVALID_DATE_RANGE",
                                    "message": "start_date must be on or before end_date",
                                }
                            },
                        },
                        "date_range_too_large": {
                            "summary": "More than 366 dates requested",
                            "value": {
                                "error": {
                                    "code": "DATE_RANGE_TOO_LARGE",
                                    "message": "Date range cannot exceed 366 days",
                                }
                            },
                        },
                    }
                }
            },
        },
        422: {
            "description": "One or more request parameters are invalid.",
            "model": ValidationErrorResponse,
        },
    },
)
def get_prayer_times_range(
    latitude: float = Query(..., ge=-90, le=90, description="Decimal latitude from -90 to 90."),
    longitude: float = Query(
        ..., ge=-180, le=180, description="Decimal longitude from -180 to 180."
    ),
    timezone: str = Query(..., description="IANA timezone, for example Asia/Dubai."),
    start_date: date = Query(..., description="First Gregorian date in the inclusive range."),
    end_date: date = Query(..., description="Last Gregorian date in the inclusive range."),
    calculation_method: CalculationMethodName = Query(
        ..., description="Islamic prayer calculation method."
    ),
    madhab: MadhabName = Query(
        default=MadhabName.SHAFI, description="Madhab used for Asr calculation."
    ),
    high_latitude_rule: HighLatitudeRuleName = Query(
        default=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
        description="Rule used when high-latitude adjustments are required.",
    ),
    fajr_adjustment: int = Query(
        default=0, ge=-1440, le=1440, description="Minutes added to Fajr Azan time."
    ),
    dhuhr_adjustment: int = Query(
        default=0, ge=-1440, le=1440, description="Minutes added to Dhuhr Azan time."
    ),
    asr_adjustment: int = Query(
        default=0, ge=-1440, le=1440, description="Minutes added to Asr Azan time."
    ),
    maghrib_adjustment: int = Query(
        default=0, ge=-1440, le=1440, description="Minutes added to Maghrib Azan time."
    ),
    isha_adjustment: int = Query(
        default=0, ge=-1440, le=1440, description="Minutes added to Isha Azan time."
    ),
) -> PrayerTimesRangeResponse:
    try:
        requested_timezone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise APIError(
            code="INVALID_TIMEZONE",
            message=f"Unknown IANA timezone: {timezone}",
            status_code=400,
        ) from exc

    adjustments = PrayerAdjustments(
        fajr=fajr_adjustment,
        dhuhr=dhuhr_adjustment,
        asr=asr_adjustment,
        maghrib=maghrib_adjustment,
        isha=isha_adjustment,
    )

    try:
        days = _range_service.calculate(
            start_date=start_date,
            end_date=end_date,
            latitude=latitude,
            longitude=longitude,
            timezone=requested_timezone,
            calculation_method=calculation_method,
            madhab=madhab,
            high_latitude_rule=high_latitude_rule,
            adjustments=adjustments,
        )
    except InvalidDateRangeError as exc:
        raise APIError("INVALID_DATE_RANGE", str(exc), 400) from exc
    except DateRangeTooLargeError as exc:
        raise APIError("DATE_RANGE_TOO_LARGE", str(exc), 400) from exc
    except ValueError as exc:
        raise APIError("INVALID_CALCULATION", str(exc), 400) from exc

    return PrayerTimesRangeResponse(
        start_date=start_date,
        end_date=end_date,
        timezone=requested_timezone.key,
        coordinates=CoordinatesResponse(latitude=latitude, longitude=longitude),
        calculation_method=calculation_method,
        madhab=madhab,
        high_latitude_rule=high_latitude_rule,
        adjustments_minutes=PrayerAdjustmentsResponse(
            fajr=fajr_adjustment,
            dhuhr=dhuhr_adjustment,
            asr=asr_adjustment,
            maghrib=maghrib_adjustment,
            isha=isha_adjustment,
        ),
        days=[
            PrayerTimesRangeDayResponse(
                date=day.result.date,
                calculated_times=CalculatedTimesResponse(
                    fajr=day.result.fajr.strftime("%H:%M"),
                    sunrise=day.result.sunrise.strftime("%H:%M"),
                    dhuhr=day.result.dhuhr.strftime("%H:%M"),
                    asr=day.result.asr.strftime("%H:%M"),
                    sunset=day.result.sunset.strftime("%H:%M"),
                    maghrib=day.result.maghrib.strftime("%H:%M"),
                    isha=day.result.isha.strftime("%H:%M"),
                ),
                azan_times=AzanTimesResponse(
                    fajr=day.azan_times["fajr"].strftime("%H:%M"),
                    dhuhr=day.azan_times["dhuhr"].strftime("%H:%M"),
                    asr=day.azan_times["asr"].strftime("%H:%M"),
                    maghrib=day.azan_times["maghrib"].strftime("%H:%M"),
                    isha=day.azan_times["isha"].strftime("%H:%M"),
                ),
            )
            for day in days
        ],
    )
