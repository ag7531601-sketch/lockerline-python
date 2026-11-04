"""Courier parcel drop endpoint."""
from fastapi import APIRouter, Response, status

from ..schemas import DropOut, DropRequest
from ..services import drops
from . import ClockDep, INTERNAL, NO_FLAT, NO_FREE_DOOR, SessionDep, SettingsDep, VALIDATION

router = APIRouter(tags=["drops"])


@router.post(
    "/drops",
    response_model=DropOut,
    status_code=status.HTTP_201_CREATED,
    summary="Book a parcel into the lowest free matching door",
    responses={400: NO_FLAT, 409: NO_FREE_DOOR, 422: VALIDATION, 500: INTERNAL},
)
def create_drop(
    body: DropRequest,
    response: Response,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> DropOut:
    result = drops.create_drop(
        session,
        body,
        clock,
        free_window_hours=settings.free_window_hours,
        code_secret=settings.code_hash_key,
    )
    response.headers["Location"] = f"/parcels/{result.parcel_id}"
    return result