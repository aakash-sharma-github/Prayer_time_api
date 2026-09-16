from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "INVALID_TIMEZONE",
                    "message": "Unknown IANA timezone: Asia/Invalid",
                }
            }
        }
    )

    error: ErrorDetail


class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    type: str


class ValidationErrorDetailResponse(ErrorDetail):
    details: list[ValidationErrorDetail]


class ValidationErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
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
    )

    error: ValidationErrorDetailResponse
