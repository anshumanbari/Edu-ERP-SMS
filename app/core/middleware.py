import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

request_logger = logging.getLogger("app.request")

# Endpoints whose responses must be left untouched (Swagger/ReDoc assets).
_EXCLUDED_PATHS = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request's method, path, response status code, and duration.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        request_logger.info(
            "%s %s -> %d (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


class StandardResponseMiddleware(BaseHTTPMiddleware):
    """
    Wraps every successful JSON response in the standard envelope:

        {"success": true, "status_code": <code>, "message": "...", "data": <body>}

    Error responses (status >= 400) already carry their own envelope from
    app.core.error_handlers and are passed through unchanged.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.url.path in _EXCLUDED_PATHS or response.status_code >= 400:
            return response

        if "application/json" not in response.headers.get("content-type", ""):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body) if body else None
        except json.JSONDecodeError:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        headers = dict(response.headers)
        headers.pop("content-length", None)

        return JSONResponse(
            status_code=response.status_code,
            headers=headers,
            content={
                "success": True,
                "status_code": response.status_code,
                "message": "Request successful.",
                "data": data,
            },
        )
