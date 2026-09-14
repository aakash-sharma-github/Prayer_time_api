from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, Query

from app.domain.prayer import (
    CalculationMethodName,
    HighLatitudeRuleName,
    MadhabName,
    PrayerCalculationRequest,
)
from app.schemas.prayer import CoordinatesResponse, PrayerTimesResponse
from app.services.prayer_calculator import PrayerCalculator

router = APIRouter(
    prefix="/api/v1",
    tags=["prayer times"],
)

_calculator = PrayerCalculator()


@router.get(
    "/prayer-times",
    response_model=PrayerTimesResponse,
    summary="Calculate prayer times",
)
def get_prayer_times(
    latitude: float = Query(
        ...,
        ge=-90,
        le=90,
        description="Latitude in decimal degrees.",
    ),
    longitude: float = Query(
        ...,
        ge=-180,
        le=180,
        description="Longitude in decimal degrees.",
    ),
    timezone: str = Query(
        ...,
        description="IANA timezone, for example Asia/Dubai.",
    ),
    date: date | None = Query(
        default=None,
        description="Gregorian calendar date. Defaults to today in the requested timezone.",
    ),
    calculation_method: CalculationMethodName = Query(
        ...,
        description="Prayer calculation method.",
    ),
    madhab: MadhabName = Query(
        default=MadhabName.SHAFI,
        description="Asr jurisprudential method.",
    ),
    high_latitude_rule: HighLatitudeRuleName = Query(
        default=HighLatitudeRuleName.MIDDLE_OF_THE_NIGHT,
        description="High-latitude adjustment rule.",
    ),
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
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

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
        times={
            "fajr": result.fajr.strftime("%H:%M"),
            "sunrise": result.sunrise.strftime("%H:%M"),
            "dhuhr": result.dhuhr.strftime("%H:%M"),
            "asr": result.asr.strftime("%H:%M"),
            "sunset": result.sunset.strftime("%H:%M"),
            "maghrib": result.maghrib.strftime("%H:%M"),
            "isha": result.isha.strftime("%H:%M"),
        },
    )
