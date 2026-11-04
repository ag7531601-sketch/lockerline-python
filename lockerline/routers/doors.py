from fastapi import APIRouter

from ..schemas import DoorOut, DoorsOut, DoorState, SizeClass
from ..services import doors
from . import ClockDep, INTERNAL, INVALID_QUERY, NO_DOOR, NO_TOWER, SessionDep

router = APIRouter(prefix="/towers/{tower}/doors", tags=["doors"])


@router.get(
    "",
    response_model=DoorsOut,
    response_model_exclude_none=True,
    summary="List and filter locker doors",
    responses={400: INVALID_QUERY, 404: NO_TOWER, 500: INTERNAL},
)
def list_doors(
    tower: str,
    session: SessionDep,
    clock: ClockDep,
    size: SizeClass | None = None,
    state: DoorState | None = None,
) -> DoorsOut:
    return doors.list_doors(session, tower, size, state, clock)


@router.get(
    "/{no}",
    response_model=DoorOut,
    response_model_exclude_none=True,
    summary="Read one locker door",
    responses={
        404: {**NO_DOOR, "description": "The tower or door does not exist"},
        500: INTERNAL,
    },
)
def get_door(tower: str, no: str, session: SessionDep, clock: ClockDep) -> DoorOut:
    return doors.get_door(session, tower, no, clock)