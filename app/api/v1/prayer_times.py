from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerAdjustments,
    PrayerCalculationRequest,
)
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
    tags=["prayer times"],
)

_calculator = PrayerCalculator()
_adjustment_service = PrayerAdjustmentService()


@router.get(
    "/prayer-times",
    response_model=PrayerTimesResponse,
    summary="Calculate prayer times",
)
def get_prayer_times(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    timezone: str = Query(..., description="IANA timezone, for example Asia/Dubai."),
    date: date | None = Query(default=None),
    calculation_method: CalculationMethodName = Query(...),
    madhab: MadhabName = Query(default=MadhabName.SHAFI),
    high_latitude_rule: HighLatitudeRuleName = Query(
        default=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT
    ),
    fajr_adjustment: int = Query(default=0, ge=-1440, le=1440),
    dhuhr_adjustment: int = Query(default=0, ge=-1440, le=1440),
    asr_adjustment: int = Query(default=0, ge=-1440, le=1440),
    maghrib_adjustment: int = Query(default=0, ge=-1440, le=1440),
    isha_adjustment: int = Query(default=0, ge=-1440, le=1440),
) -> PrayerTimesResponse:
    try:
        requested_timezone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown IANA timezone: {timezone}",
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
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
