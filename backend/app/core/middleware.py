import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add a unique request ID to each request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        # Update request state
        request.state.request_id = request_id
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware to log request details and timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Get request ID from state (added by RequestIDMiddleware) or generate new one
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

        # Log request
        logger.info(f"[{request_id}] Request: {request.method} {request.url.path}")

        # Process request and catch any exceptions to ensure logging
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(
                f"[{request_id}] Response: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Took: {process_time:.4f}s"
            )

            # Add processing time header
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] Error: {request.method} {request.url.path} "
                f"- Took: {process_time:.4f}s - Error: {str(e)}"
            )
            raise


def setup_middleware(app: FastAPI) -> None:
    """Configure middleware for the application."""

    # Request ID middleware (Add first so all other middleware can access it)
    app.add_middleware(RequestIDMiddleware)

    # Request logger middleware
    if not settings.DEBUG:  # Avoid double-logging in debug mode with uvicorn
        app.add_middleware(RequestLoggerMiddleware)

    # CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # GZIP compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB
