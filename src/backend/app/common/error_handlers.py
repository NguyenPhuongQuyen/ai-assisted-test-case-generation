import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.constants import ErrorCode
from app.common.exceptions import AppError

logger = logging.getLogger(__name__)


def _error_response(status_code: int, code: str, message: str, details: list[dict[str, str]]) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register one global error boundary so every backend error follows ER-05."""

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code.value, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error.get("loc", [])[1:]) or "request",
                "issue": str(error.get("msg", "invalid value")),
            }
            for error in exc.errors()
        ]
        return _error_response(422, ErrorCode.VALIDATION_ERROR.value, "Dữ liệu đầu vào không hợp lệ.", details)

    @app.exception_handler(HTTPException)
    async def http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        code = ErrorCode.UNAUTHORIZED.value if exc.status_code == 401 else ErrorCode.CONFLICT.value
        return _error_response(exc.status_code, code, str(exc.detail), [])

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # ER-04/ER-07: keep sensitive server details in logs, never expose stack trace, SQL, token or request body.
        logger.exception(
            "Unhandled server error",
            extra={"path": request.url.path, "operation": "request"},
        )
        return _error_response(
            500,
            ErrorCode.INTERNAL_SERVER_ERROR.value,
            "Đã xảy ra lỗi phía máy chủ.",
            [],
        )
