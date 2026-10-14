import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.attendance import CloseReason


class CheckInIn(BaseModel):
    gym_id: uuid.UUID
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float = Field(ge=0, le=100_000, description="Phone-reported GPS error, metres")


class AttendanceOut(BaseModel):
    id: uuid.UUID
    gym_id: uuid.UUID
    gym_name: str
    check_in_at: datetime
    check_out_at: datetime | None
    close_reason: CloseReason | None
    # When an open session will be closed automatically if the user forgets to check out.
    auto_close_at: datetime
    duration_minutes: int


class CurrentAttendanceOut(BaseModel):
    session: AttendanceOut | None


class OccupancyOut(BaseModel):
    current: int
    maximum_capacity: int | None
    percent: int | None
    level: Literal["low", "medium", "high"] | None
