"""The one place that turns every error into application/problem+json."""
from http import HTTPStatus
import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import (
    HTTP,
    METHOD_NOT_ALLOWED,
    NOT_FOUND,
    PROBLEM,
    VALIDATION_BODY,
    VALIDATION_PARAMS,
    DomainError,
)


def problem(
    status: int,
    type_: str,
    title: str,
    detail: str,
    headers: dict | None = None,
    **extra,
) -> JSONResponse:
    body = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        **extra,
    }
    return JSONResponse(
        status_code=status,
        content=body,
        media_type=PROBLEM,
        headers=headers,
    )


logger = logging.getLogger("lockerline")


async def _handle_error(request: Request, exc: Exception):
    """Map application and framework errors to the shared problem format."""
    if isinstance(exc, DomainError):
        return problem(exc.status, exc.type, exc.title, exc.detail, **exc.extra)

    if isinstance(exc, RequestValidationError):
        raw_errors = exc.errors()
        errors = [
            {
                "field": ".".join(
                    str(part)
                    for part in error["loc"]
                    if part not in ("body", "query", "path")
                ),
                "message": error["msg"],
            }
            for error in raw_errors
        ]
        in_body = any(
            error["loc"] and error["loc"][0] == "body"
            for error in raw_errors
        )
        status, type_, title = (
            VALIDATION_BODY if in_body else VALIDATION_PARAMS
        )
        return problem(
            status,
            type_,
            title,
            f"{len(errors)} field(s) failed validation",
            errors=errors,
        )

    if isinstance(exc, StarletteHTTPException):
        headers = dict(exc.headers) if exc.headers else None

        if exc.status_code == 404:
            status, type_, title = NOT_FOUND
            return problem(
                status,
                type_,
                title,
                f"Nothing is served at {request.url.path}",
                headers,
            )

        if exc.status_code == 405:
            status, type_, title = METHOD_NOT_ALLOWED
            return problem(
                status,
                type_,
                title,
                f"{request.method} is not allowed on {request.url.path}",
                headers,
            )

        try:
            phrase = HTTPStatus(exc.status_code).phrase
        except ValueError:
            phrase = "HTTP error"

        return problem(
            exc.status_code,
            HTTP,
            phrase,
            str(exc.detail),
            headers,
        )

    request_id = getattr(request.state, "request_id", uuid4().hex)
    logger.error(
        "request request_id=%s method=%s path=%s status=500 error=%s",
        request_id,
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return problem(
        500,
        "/errors/internal",
        "Internal server error",
        "An unexpected error occurred",
        headers={"X-Request-ID": request_id},
        request_id=request_id,
    )


def install_handlers(app: FastAPI) -> None:
    """Register one handler implementation for each exception family."""
    app.add_exception_handler(DomainError, _handle_error)
    app.add_exception_handler(RequestValidationError, _handle_error)
    app.add_exception_handler(StarletteHTTPException, _handle_error)
    app.add_exception_handler(Exception, _handle_error)