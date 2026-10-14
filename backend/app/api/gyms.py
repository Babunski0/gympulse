import uuid

from fastapi import APIRouter, Query

from app.api.deps import DB, AdminUser, AppAdminUser, CurrentUser
from app.models import Gym
from app.schemas.attendance import OccupancyOut
from app.schemas.gyms import (
    GymCreateIn,
    GymOut,
    GymUpdateIn,
    MemberOut,
    MembershipOut,
    MembershipUpdateIn,
    MyGymOut,
)
from app.services import attendance as attendance_service
from app.services import geocoding
from app.services import gyms as gym_service

router = APIRouter(tags=["gyms"])


def with_occupancy(db: DB, gyms: list[Gym]) -> list[GymOut]:
    counts = attendance_service.occupancy_counts(db, [g.id for g in gyms])
    return [
        GymOut.model_validate(g).model_copy(
            update={"occupancy": attendance_service.occupancy(counts[g.id], g.maximum_capacity)}
        )
        for g in gyms
    ]


@router.get("/gyms", response_model=list[GymOut])
def list_gyms(
    db: DB,
    _: CurrentUser,
    q: str | None = Query(default=None, max_length=100),
    city: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return with_occupancy(db, gym_service.list_gyms(db, q, city, limit, offset))


@router.get("/gyms/cities", response_model=list[str])
def list_cities(db: DB, _: CurrentUser):
    return gym_service.list_cities(db)


@router.get("/geocode", response_model=geocoding.GeocodeResult)
def geocode(
    _: AdminUser,
    q: str = Query(min_length=2, max_length=200),
    kind: geocoding.Kind = "address",
):
    """Admin gym form: find a city or street address on the map."""
    return geocoding.geocode(q, kind)


@router.post("/gyms", status_code=201, response_model=GymOut)
def create_gym(body: GymCreateIn, db: DB, admin: AppAdminUser):
    return gym_service.create_gym(db, admin, body)


@router.get("/gyms/{gym_id}", response_model=GymOut)
def get_gym(gym_id: uuid.UUID, db: DB, _: CurrentUser):
    return with_occupancy(db, [gym_service.get_gym(db, gym_id)])[0]


@router.get("/gyms/{gym_id}/occupancy", response_model=OccupancyOut)
def get_occupancy(gym_id: uuid.UUID, db: DB, _: CurrentUser):
    """US-07: how many members are checked in right now."""
    return with_occupancy(db, [gym_service.get_gym(db, gym_id)])[0].occupancy


@router.patch("/gyms/{gym_id}", response_model=GymOut)
def update_gym(gym_id: uuid.UUID, body: GymUpdateIn, db: DB, admin: AdminUser):
    return gym_service.update_gym(db, admin, gym_id, body)


@router.post("/gyms/{gym_id}/memberships", status_code=201, response_model=MembershipOut)
def join_gym(gym_id: uuid.UUID, db: DB, user: CurrentUser):
    return gym_service.join_gym(db, user, gym_id)


@router.get("/gyms/{gym_id}/memberships", response_model=list[MemberOut])
def list_members(gym_id: uuid.UUID, db: DB, admin: AdminUser):
    return [
        MemberOut(
            **MembershipOut.model_validate(m).model_dump(),
            email=u.email,
            full_name=u.full_name,
        )
        for m, u in gym_service.list_members(db, admin, gym_id)
    ]


@router.patch("/gyms/{gym_id}/memberships/{membership_id}", response_model=MembershipOut)
def update_membership(
    gym_id: uuid.UUID,
    membership_id: uuid.UUID,
    body: MembershipUpdateIn,
    db: DB,
    admin: AdminUser,
):
    return gym_service.set_membership_status(db, admin, gym_id, membership_id, body.status)


@router.get("/me/gyms", response_model=list[MyGymOut])
def my_gyms(db: DB, user: CurrentUser):
    rows = gym_service.my_gyms(db, user)
    gyms = with_occupancy(db, [g for g, _ in rows])
    return [
        MyGymOut(gym=gym, membership=MembershipOut.model_validate(m))
        for gym, (_, m) in zip(gyms, rows, strict=True)
    ]


@router.get("/admin/gyms", response_model=list[GymOut])
def managed_gyms(db: DB, admin: AdminUser):
    return with_occupancy(db, gym_service.managed_gyms(db, admin))
