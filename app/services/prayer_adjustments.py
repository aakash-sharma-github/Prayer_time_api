from datetime import datetime

from app.domain.prayer import PrayerAdjustments, PrayerTimesResult


class PrayerAdjustmentService:
    """Apply API-level Azan adjustments to calculated prayer times."""

    def apply(
        self,
        prayer_times: PrayerTimesResult,
        adjustments: PrayerAdjustments,
    ) -> dict[str, datetime]:
        return adjustments.apply(prayer_times)
