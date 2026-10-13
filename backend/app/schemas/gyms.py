import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.gym import MembershipStatus
from app.schemas.common import ORMModel

Name = Annotated[str, Field(min_length=1, max_length=120)]
Address = Annotated[str, Field(min_length=1, max_length=255)]
Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]
Radius = Annotated[int, Field(ge=25, le=2000)]  # NFR-09: meaningful geofence range in metres
Capacity = Annotated[int, Field(ge=1, le=10_000)]


class GymCreateIn(BaseModel):
    name: Name
    address: Address
    latitude: Latitude
    longitude: Longitude
    radius_m: Radius | None = None  # server default when omitted
    maximum_capacity: Capacity | None = None
    membership_requires_approval: bool = False


class GymUpdateIn(BaseModel):
    """Partial update: only fields present in the request are changed."""

    name: Name | None = None
    address: Address | None = None
    latitude: Latitude | None = None
    longitude: Longitude | None = None
    radius_m: Radius | None = None
    maximum_capacity: Capacity | None = None  # explicit null clears the capacity
    membership_requires_approval: bool | None = None
    is_active: bool | None = None


class GymOut(ORMModel):
    id: uuid.UUID
    name: str
    address: str
    latitude: float
    longitude: float
    radius_m: int
    maximum_capacity: int | None
    membership_requires_approval: bool
    is_active: bool


class MembershipOut(ORMModel):
    id: uuid.UUID
    gym_id: uuid.UUID
    user_id: uuid.UUID
    status: MembershipStatus
    created_at: datetime


class MemberOut(MembershipOut):
    email: str
    full_name: str


class MyGymOut(BaseModel):
    gym: GymOut
    membership: MembershipOut


class MembershipUpdateIn(BaseModel):
    status: MembershipStatus
