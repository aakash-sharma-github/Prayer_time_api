from fastapi import APIRouter

from app.domain.prayer import CalculationMethodName, HighLatitudeRuleName, MadhabName
from app.schemas.prayer import CalculationMethodsResponse

router = APIRouter(prefix="/api/v1", tags=["Prayer times"])


@router.get(
    "/calculation-methods",
    response_model=CalculationMethodsResponse,
    summary="List supported prayer calculation settings",
    response_description="Calculation methods, Madhabs, and high-latitude rules accepted by v1.",
)
def get_calculation_methods() -> CalculationMethodsResponse:
    """Return the enums used to validate both prayer-time endpoints."""
    return CalculationMethodsResponse(
        calculation_methods=list(CalculationMethodName),
        madhabs=list(MadhabName),
        high_latitude_rules=list(HighLatitudeRuleName),
    )
