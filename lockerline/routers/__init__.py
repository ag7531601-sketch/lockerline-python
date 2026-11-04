"""One router per resource. Routes parse and delegate; they hold no rules. The request-scoped dependencies
(session, clock, settings) are declared here so the services never see the web framework."""
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..clock import Clock, get_clock
from ..db import get_session
from ..settings import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


SessionDep = Annotated[Session, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


# Shared OpenAPI examples. Kept in this package module so resource routers don't
# depend on an extra module that may be omitted by file-based runners.
PROBLEM = "application/problem+json"


def problem_response(description: str, type_: str, title: str, detail: str, *, status: int = 400, **extra) -> dict:
    example = {"type": type_, "title": title, "status": status, "detail": detail, **extra}
    return {"description": description, "content": {PROBLEM: {"example": example}}}


VALIDATION = problem_response(
    "The request body is invalid",
    "/errors/validation",
    "The request body is not valid",
    "1 field(s) failed validation",
    status=422,
    errors=[{"field": "size_class", "message": "Input should be 'S', 'M' or 'L'"}],
)
INVALID_QUERY = problem_response(
    "A query parameter is invalid",
    "/errors/validation",
    "Invalid query parameter",
    "1 field(s) failed validation",
    status=400,
    errors=[{"field": "size", "message": "Input should be 'S', 'M' or 'L'"}],
)
NO_TOWER = problem_response(
    "The tower does not exist",
    "/errors/no-such-tower",
    "No such tower",
    "Tower 'Z' does not exist",
    status=404,
)
NO_DOOR = problem_response(
    "The door does not exist",
    "/errors/no-such-door",
    "No such door",
    "Door 'D99' does not exist in tower 'A'",
    status=404,
)
NO_FLAT = problem_response(
    "The flat does not exist",
    "/errors/no-such-flat",
    "No such flat",
    "Flat '999' does not exist in tower 'A'",
    status=400,
)
NO_FREE_DOOR = problem_response(
    "No door of the requested size is free",
    "/errors/no-door-free",
    "No door free",
    "No free door of size L",
    status=409,
    free_sizes=["S", "M"],
)
NO_PARCEL = problem_response(
    "The parcel does not exist",
    "/errors/no-such-parcel",
    "No such parcel",
    "Parcel 'P999' does not exist",
    status=404,
)
NO_CODE = problem_response(
    "The code does not exist",
    "/errors/no-such-code",
    "No such code",
    "No parcel matches that code",
    status=404,
)
EXPIRED = problem_response(
    "The code has expired",
    "/errors/code-expired",
    "Code has expired",
    "The pickup window has passed",
    status=404,
)
USED = problem_response(
    "The code was already used",
    "/errors/code-used",
    "Code has already been used",
    "The code has already opened its door",
    status=409,
)
INTERNAL = problem_response(
    "An unexpected server error occurred",
    "/errors/internal",
    "Internal server error",
    "An unexpected error occurred",
    status=500,
    request_id="a per-request identifier",
)