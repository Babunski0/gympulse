import uuid

from fastapi import APIRouter, Query

from app.api.deps import DB, AdminUser, CurrentUser
from app.schemas.gyms import (
    GymCreateIn,
    GymOut,
    GymUpdateIn,
    MemberOut,
    MembershipOut,
    MembershipUpdateIn,
    MyGymOut,
)
from app.services import gyms as gym_service

router = APIRouter(tags=["gyms"])


@router.get("/gyms", response_model=list[GymOut])
def list_gyms(
    db: DB,
    _: CurrentUser,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return gym_service.list_gyms(db, q, limit, offset)


@router.post("/gyms", status_code=201, response_model=GymOut)
def create_gym(body: GymCreateIn, db: DB, admin: AdminUser):
    return gym_service.create_gym(db, admin, body)


@router.get("/gyms/{gym_id}", response_model=GymOut)
def get_gym(gym_id: uuid.UUID, db: DB, _: CurrentUser):
    return gym_service.get_gym(db, gym_id)


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
    return [
        MyGymOut(gym=GymOut.model_validate(g), membership=MembershipOut.model_validate(m))
        for g, m in gym_service.my_gyms(db, user)
    ]


@router.get("/admin/gyms", response_model=list[GymOut])
def managed_gyms(db: DB, admin: AdminUser):
    return gym_service.managed_gyms(db, admin)
