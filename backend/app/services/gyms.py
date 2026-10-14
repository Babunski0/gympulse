import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, forbidden, not_found
from app.models import AttendanceSession, Gym, GymAdmin, GymMembership, User
from app.models._base import utcnow
from app.models.attendance import CloseReason
from app.models.gym import MembershipStatus
from app.models.user import Role
from app.schemas.gyms import GymCreateIn, GymUpdateIn


def get_gym(db: Session, gym_id: uuid.UUID, *, include_inactive: bool = False) -> Gym:
    gym = db.get(Gym, gym_id)
    if gym is None or (not gym.is_active and not include_inactive):
        raise not_found("gym")
    return gym


def is_gym_admin(db: Session, user: User, gym_id: uuid.UUID) -> bool:
    return (
        db.scalar(select(GymAdmin.id).where(GymAdmin.gym_id == gym_id, GymAdmin.user_id == user.id))
        is not None
    )


def get_managed_gym(db: Session, user: User, gym_id: uuid.UUID) -> Gym:
    """NFR-03: a gym admin may only touch gyms they manage; the app admin manages all."""
    gym = get_gym(db, gym_id, include_inactive=True)
    if user.role != Role.APP_ADMIN and not is_gym_admin(db, user, gym_id):
        raise forbidden("You are not an administrator of this gym.")
    return gym


def normalize_city(city: str) -> str:
    """'  podgorica ' -> 'Podgorica', so the same city is not listed twice."""
    city = " ".join(city.split())
    return city[:1].upper() + city[1:]


def list_gyms(db: Session, q: str | None, city: str | None, limit: int, offset: int) -> list[Gym]:
    stmt = select(Gym).where(Gym.is_active.is_(True))
    if city:
        stmt = stmt.where(func.lower(Gym.city) == normalize_city(city).lower())
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Gym.name.ilike(pattern), Gym.address.ilike(pattern), Gym.city.ilike(pattern))
        )
    return list(db.scalars(stmt.order_by(Gym.name).limit(limit).offset(offset)))


def list_cities(db: Session) -> list[str]:
    return list(
        db.scalars(select(Gym.city).where(Gym.is_active.is_(True)).distinct().order_by(Gym.city))
    )


def create_gym(db: Session, admin: User, data: GymCreateIn) -> Gym:
    values = data.model_dump()
    values["city"] = normalize_city(values["city"])
    values["radius_m"] = values["radius_m"] or get_settings().default_gym_radius_m
    gym = Gym(**values)
    db.add(gym)
    db.flush()
    db.add(GymAdmin(gym_id=gym.id, user_id=admin.id))
    db.commit()
    return gym


def update_gym(db: Session, admin: User, gym_id: uuid.UUID, data: GymUpdateIn) -> Gym:
    gym = get_managed_gym(db, admin, gym_id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("city"):
        changes["city"] = normalize_city(changes["city"])
    for field in (
        "name",
        "address",
        "city",
        "latitude",
        "longitude",
        "radius_m",
        "is_active",
        "membership_requires_approval",
    ):
        if field in changes and changes[field] is None:
            raise AppError(422, "validation_error", f"{field} cannot be null.")
    for field, value in changes.items():
        setattr(gym, field, value)
    db.commit()
    return gym


def delete_gym(db: Session, gym_id: uuid.UUID) -> None:
    """App admin only. Memberships, gym admins and visit history go with it (DB cascade)."""
    gym = get_gym(db, gym_id, include_inactive=True)
    db.delete(gym)
    db.commit()


def join_gym(db: Session, user: User, gym_id: uuid.UUID) -> GymMembership:
    gym = get_gym(db, gym_id)
    status = (
        MembershipStatus.PENDING if gym.membership_requires_approval else MembershipStatus.ACTIVE
    )
    existing = db.scalar(
        select(GymMembership).where(
            GymMembership.gym_id == gym_id, GymMembership.user_id == user.id
        )
    )
    if existing is not None:
        if existing.status != MembershipStatus.REJECTED:
            raise AppError(409, "already_member", "You already joined or requested this gym.")
        existing.status = status  # a rejected member may ask again
        db.commit()
        return existing
    membership = GymMembership(user_id=user.id, gym_id=gym.id, status=status)
    db.add(membership)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "already_member", "You already joined or requested this gym.") from None
    return membership


def leave_gym(db: Session, user: User, gym_id: uuid.UUID) -> None:
    """Leave a gym or withdraw a pending request; an open visit there is checked out first."""
    membership = db.scalar(
        select(GymMembership).where(
            GymMembership.gym_id == gym_id, GymMembership.user_id == user.id
        )
    )
    if membership is None:
        raise not_found("membership")
    open_visit = db.scalar(
        select(AttendanceSession).where(
            AttendanceSession.user_id == user.id,
            AttendanceSession.gym_id == gym_id,
            AttendanceSession.check_out_at.is_(None),
        )
    )
    if open_visit is not None:
        open_visit.check_out_at = utcnow()
        open_visit.close_reason = CloseReason.USER
    db.delete(membership)
    db.commit()


def managed_gyms(db: Session, admin: User) -> list[Gym]:
    if admin.role == Role.APP_ADMIN:
        return list(db.scalars(select(Gym).order_by(Gym.city, Gym.name)))
    return list(
        db.scalars(
            select(Gym)
            .join(GymAdmin, GymAdmin.gym_id == Gym.id)
            .where(GymAdmin.user_id == admin.id)
            .order_by(Gym.name)
        )
    )


def my_gyms(db: Session, user: User) -> list[tuple[Gym, GymMembership]]:
    rows = db.execute(
        select(Gym, GymMembership)
        .join(GymMembership, GymMembership.gym_id == Gym.id)
        .where(GymMembership.user_id == user.id, Gym.is_active.is_(True))
        .order_by(Gym.name)
    )
    return [(g, m) for g, m in rows]


def list_members(db: Session, admin: User, gym_id: uuid.UUID) -> list[tuple[GymMembership, User]]:
    get_managed_gym(db, admin, gym_id)
    rows = db.execute(
        select(GymMembership, User)
        .join(User, User.id == GymMembership.user_id)
        .where(GymMembership.gym_id == gym_id)
        .order_by(GymMembership.created_at)
    )
    return [(m, u) for m, u in rows]


def set_membership_status(
    db: Session, admin: User, gym_id: uuid.UUID, membership_id: uuid.UUID, status: str
) -> GymMembership:
    get_managed_gym(db, admin, gym_id)
    membership = db.get(GymMembership, membership_id)
    if membership is None or membership.gym_id != gym_id:
        raise not_found("membership")
    membership.status = status
    db.commit()
    return membership


def has_active_membership(db: Session, user: User, gym_id: uuid.UUID) -> bool:
    return (
        db.scalar(
            select(GymMembership.id).where(
                GymMembership.gym_id == gym_id,
                GymMembership.user_id == user.id,
                GymMembership.status == MembershipStatus.ACTIVE,
            )
        )
        is not None
    )
