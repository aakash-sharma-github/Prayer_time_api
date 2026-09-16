from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.errors import ErrorResponse, ValidationErrorResponse


class APIError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def api_error_handler(
        request: Request,
        exc: APIError,
    ) -> JSONResponse:
        response = ErrorResponse(
            error={
                "code": exc.code,
                "message": exc.message,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        response = ValidationErrorResponse(
            error={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": [
                    {
                        "field": ".".join(str(part) for part in error["loc"]),
                        "message": error["msg"],
                        "type": error["type"],
                    }
                    for error in exc.errors()
                ],
            }
        )

        return JSONResponse(
            status_code=422,
            content=response.model_dump(),
        )
