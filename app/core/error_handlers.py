import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger("app.error")


def _error_response(status_code: int, error_code: str, message: str, details=None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "status_code": status_code,
            "error": error_code,
            "message": message,
            "details": details,
        },
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("%s %s -> %s: %s", request.method, request.url.path, exc.error_code, exc.message)
    return _error_response(exc.status_code, exc.error_code, exc.message)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.warning("%s %s -> HTTP_ERROR %s: %s", request.method, request.url.path, exc.status_code, exc.detail)
    return _error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning("%s %s -> VALIDATION_ERROR: %s", request.method, request.url.path, exc.errors())
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "VALIDATION_ERROR",
        "Request validation failed.",
        details=jsonable_encoder(exc.errors()),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("%s %s -> unhandled exception", request.method, request.url.path, exc_info=exc)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "INTERNAL_SERVER_ERROR",
        "An unexpected error occurred.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Wire up the centralized exception handlers on the FastAPI app.

    Registration order does not matter to Starlette — it always dispatches
    on the most specific exception class registered.
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
