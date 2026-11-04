"""Pickup endpoint: collect a parcel and free its door."""
from fastapi import APIRouter

from ..ids import parcel_public
from ..schemas import PickupOut, PickupRequest
from ..services.pickups import pickup
from . import ClockDep, EXPIRED, INTERNAL, NO_CODE, SessionDep, SettingsDep, USED, VALIDATION

router = APIRouter(tags=["pickups"])


@router.post(
    "/pickups",
    response_model=PickupOut,
    summary="Open a parcel door with its pickup code",
    responses={
        404: {
            "description": "The code does not exist or has expired",
            "content": {
                "application/problem+json": {
                    "examples": {
                        "unknownCode": {
                            "summary": "Unknown code",
                            "value": NO_CODE["content"]["application/problem+json"]["example"],
                        },
                        "expiredCode": {
                            "summary": "Expired code",
                            "value": EXPIRED["content"]["application/problem+json"]["example"],
                        },
                    }
                }
            },
        },
        409: USED,
        422: VALIDATION,
        500: INTERNAL,
    },
)
def collect_pickup(
    body: PickupRequest,
    session: SessionDep,
    clock: ClockDep,
    settings: SettingsDep,
) -> PickupOut:
    parcel, door = pickup(session, body, clock, settings.code_hash_key)
    return PickupOut(
        parcel_id=parcel_public(parcel.id),
        door=door.no,
        opened_at=parcel.collected_at,
        dwell_seconds=parcel.dwell_seconds,
    )