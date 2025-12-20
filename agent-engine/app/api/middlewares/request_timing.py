# app/api/middleware/request_timing.py (or wherever)
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

access_logger = logging.getLogger("app.access")

class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0

        client = request.client.host if request.client else "-"
        port = request.client.port if request.client else 0
        client_addr = f"{client}:{port}"

        method = request.method
        full_path = request.url.path
        if request.url.query:
            full_path = f"{full_path}?{request.url.query}"

        http_version = request.scope.get("http_version", "1.1")
        status_code = response.status_code

        access_logger.info(
            "%s %s %s %s %s",
            client_addr,
            method,
            full_path,
            http_version,
            status_code,
            extra={"duration_ms": duration_ms},
        )

        return response
