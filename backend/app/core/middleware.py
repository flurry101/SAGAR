# attr: m1
# [application middlewares and global exception handling]
from __future__ import annotations

import uuid
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.exceptions import OrcaException
from app.schemas.common import ErrorResponse, ErrorDetails, Meta

logger = logging.getLogger(__name__)


async def add_request_id_middleware(request: Request, call_next: Callable) -> Response:
    # [extract or assign unique x-request-id for end to end tracing]
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
    # [add recommended security headers including cache controls for auth endpoints]
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    path = request.url.path
    if "/login" in path or "/auth" in path:
        response.headers["Cache-Control"] = "no-store"
        
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # [format standard fastapi httpexception into errorresponse envelope while retaining detail for test compat]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    content = {
        "status": "error",
        "detail": str(exc.detail),
        "error": {
            "code": "HTTP_ERROR",
            "message": str(exc.detail),
            "details": None,
        },
        "meta": {
            "request_id": request_id,
            "version": "v1",
        },
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={"X-Request-ID": request_id},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # [format pydantic request validation error into errorresponse envelope]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    content = {
        "status": "error",
        "detail": exc.errors(),
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
            "details": exc.errors(),
        },
        "meta": {
            "request_id": request_id,
            "version": "v1",
        },
    }
    return JSONResponse(
        status_code=422,
        content=content,
        headers={"X-Request-ID": request_id},
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # [format all other exceptions into standardized errorresponse envelope]
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    if isinstance(exc, OrcaException):
        logger.warning(f"OrcaException [{exc.error_code}] on {request.url.path}: {exc.message}")
        content = {
            "status": "error",
            "detail": exc.message,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
            "meta": {
                "request_id": request_id,
                "version": "v1",
            },
        }
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers={"X-Request-ID": request_id},
        )

    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    content = {
        "status": "error",
        "detail": "An unexpected server error occurred.",
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected server error occurred.",
            "details": str(exc) if logger.isEnabledFor(logging.DEBUG) else None,
        },
        "meta": {
            "request_id": request_id,
            "version": "v1",
        },
    }
    return JSONResponse(
        status_code=500,
        content=content,
        headers={"X-Request-ID": request_id},
    )
# attr: m1

