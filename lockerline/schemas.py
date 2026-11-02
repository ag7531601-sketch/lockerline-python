"""Validated request and response models."""
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

SizeClass = Literal["S", "M", "L"]
DoorState = Literal["free", "holding"]
EventKind = Literal["dropped", "code_issued", "opened"]


def _iso_z(dt: datetime) -> str:
    """SQLite hands naive datetimes back; everything the app stores is UTC, so a naive value is UTC, never local time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


UtcZ = Annotated[datetime, PlainSerializer(_iso_z, return_type=str)]


class DropRequest(BaseModel):
    size_class: SizeClass
    flat: str = Field(min_length=1, max_length=8, pattern=r"^\d+$")


class DropOut(BaseModel):
    parcel_id: str
    door: str
    size_class: SizeClass
    flat: str
    dropped_at: UtcZ
    code: str = Field(pattern=r"^\d{6}$")
    expires_at: UtcZ


class PickupRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class PickupOut(BaseModel):
    parcel_id: str
    door: str
    opened_at: UtcZ
    dwell_seconds: int


class EventOut(BaseModel):
    """One line of a parcel's history. `door` on dropped and opened, `expires_at` on code_issued,
    `dwell_seconds` on opened — the facts the event row stores, never the code or a name."""
    model_config = ConfigDict(extra="forbid")

    at: UtcZ
    kind: EventKind
    door: str | None = None
    expires_at: UtcZ | None = None
    dwell_seconds: int | None = None


class ParcelOut(BaseModel):
    parcel_id: str
    door: str
    size_class: SizeClass
    flat: str
    state: Literal["holding", "collected"]
    dropped_at: UtcZ
    events: list[EventOut]


class DoorListItem(BaseModel):
    """One cell of the wall. A free door carries only no, size and state; a holding door adds its parcel and dwell."""
    no: str
    size: SizeClass
    state: DoorState
    parcel_id: str | None = None
    dwell_seconds: int | None = None


class DoorOut(DoorListItem):
    """One door, read on its own: a holding door also names the flat its parcel is for."""
    flat: str | None = None


class DoorsOut(BaseModel):
    tower: str
    free: int = Field(description="How many of the doors in this answer (after the filters) are free")
    doors: list[DoorListItem]