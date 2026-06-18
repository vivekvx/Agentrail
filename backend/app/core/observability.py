from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

access_logger = logging.getLogger("agentrail.access")


def configure_logging(level: str = "INFO") -> None:
    """Set up root logging once. Idempotent across reloads."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log one line per request: method, path, status, latency."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            access_logger.exception(
                "%s %s -> 500 (%.1fms)", request.method, request.url.path, elapsed_ms
            )
            raise
        elapsed_ms = (time.perf_counter() - start) * 1000
        access_logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
