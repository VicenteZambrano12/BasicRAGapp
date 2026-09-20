"""Request/response logging middleware with correlation id propagation."""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.utils.observability.logger import reset_correlation_id, set_correlation_id

logger = logging.getLogger(__name__)

CORRELATION_ID_HEADER = "X-Request-ID"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every incoming request/outgoing response and tags them with a correlation id."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get(CORRELATION_ID_HEADER)
        correlation_id, token = set_correlation_id(incoming_id)
        client_ip = request.client.host if request.client else "-"
        start_time = time.perf_counter()

        logger.info(
            "Request started",
            extra={
                "event": "request_started",
                "http_method": request.method,
                "path": request.url.path,
                "client_ip": client_ip,
            },
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "Request failed with an unhandled exception",
                exc_info=True,
                extra={
                    "event": "request_failed",
                    "http_method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "duration_ms": duration_ms,
                },
            )
            raise
        else:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                "Request completed",
                extra={
                    "event": "request_completed",
                    "http_method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response
        finally:
            reset_correlation_id(token)
