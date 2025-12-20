from __future__ import annotations

import logging
import traceback
import uuid
from typing import Optional

from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("app")


class GlobalExceptionHandler:
    """
    Global exception middleware that turns unhandled exceptions into RFC7807 Problem Details.

    - Only handles unexpected/unhandled exceptions => 500
    - Excludes FastAPI validation exceptions (RequestValidationError)
    - Adds correlation header: X-Error-Id
    - Logs the exception with stack trace
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        instance_base_url: Optional[str] = None,
        include_traceback: bool = False,
        error_header_name: str = "X-Error-Id",
    ) -> None:
        self.app = app
        self.instance_base_url = instance_base_url
        self.include_traceback = include_traceback
        self.error_header_name = error_header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        error_id = str(uuid.uuid4())
        started = False

        async def send_wrapper(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)

        except RequestValidationError:
            raise

        except Exception as exc:
            logger.exception(
                "Unhandled exception (error_id=%s) %s %s",
                error_id,
                scope.get("method"),
                scope.get("path"),
                extra={
                    "error_id": error_id,
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                },
            )

            if started:
                raise

            method = scope.get("method", "")
            path = scope.get("path", "")
            instance = f"{self.instance_base_url}{path}" if self.instance_base_url else path

            problem = {
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred.",
                "instance": instance,
                "errorId": error_id,
            }

            if self.include_traceback:
                problem["trace"] = traceback.format_exception(type(exc), exc, exc.__traceback__)

            response = JSONResponse(
                status_code=500,
                content=problem,
                media_type="application/problem+json",
                headers={self.error_header_name: error_id},
            )
            await response(scope, receive, send)
