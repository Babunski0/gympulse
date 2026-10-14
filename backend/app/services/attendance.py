"""Gym visits: GPS check-in, check-out, forgotten sessions and live occupancy."""

import math
import uuid
from collections.abc import Iterable
from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, forbidden
from app.models import AttendanceSession, Gym, User
from app.models._base import utcnow
from app.models.attendance import CloseReason
from app.schemas.attendance import CheckInIn, OccupancyOut
from app.services import gyms as gym_service

EARTH_RADIUS_M = 6_371_000


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle (haversine) distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def max_duration() -> timedelta:
    return timedelta(hours=get_settings().attendance_max_hours)


def expire_stale_sessions(db: Session) -> int:
    """ATT-05: close sessions that outlived the allowed visit length.

    The visit is recorded as ending at the limit, not now, so a forgotten check-out does not
    count as a day in the gym. Runs before every attendance or occupancy read, so no separate
    scheduler is needed; `python -m app.cli expire-sessions` does the same on demand.
    """
    limit = max_duration()
    result = db.execute(
        update(AttendanceSession)
        .where(
            AttendanceSession.check_out_at.is_(None),
            AttendanceSession.check_in_at < utcnow() - limit,
        )
        .values(
            check_out_at=AttendanceSession.check_in_at + limit,
            close_reason=CloseReason.AUTO_EXPIRED,
        )
    )
    db.commit()
    return result.rowcount


def active_session(db: Session, user: User) -> AttendanceSession | None:
    return db.scalar(
        select(AttendanceSession).where(
            AttendanceSession.user_id == user.id, AttendanceSession.check_out_at.is_(None)
        )
    )


def _already_checked_in() -> AppError:
    return AppError(409, "already_checked_in", "You are already checked in. Check out first.")


def check_in(db: Session, user: User, data: CheckInIn) -> tuple[AttendanceSession, Gym]:
    settings = get_settings()
    expire_stale_sessions(db)
    gym = gym_service.get_gym(db, data.gym_id)
    if not gym_service.has_active_membership(db, user, gym.id):
        raise forbidden("Join this gym (and wait for approval if needed) before checking in.")
    if active_session(db, user) is not None:
        raise _already_checked_in()
    if data.accuracy_m > settings.checkin_max_accuracy_m:  # ATT-02
        raise AppError(
            422,
            "location_inaccurate",
            "Your location is not precise enough. Go outside or wait a moment and try again.",
            {"accuracy_m": round(data.accuracy_m)},
        )
    # Coordinates are only used for this check and never stored (NFR-02).
    distance = distance_m(data.latitude, data.longitude, gym.latitude, gym.longitude)
    allowed = gym.radius_m + min(data.accuracy_m, settings.checkin_accuracy_allowance_m)
    if distance > allowed:
        raise AppError(
            403,
            "outside_gym_radius",
            "You are too far from the gym to check in.",
            {"distance_m": round(distance), "radius_m": gym.radius_m},
        )
    session = AttendanceSession(user_id=user.id, gym_id=gym.id, check_in_at=utcnow())
    db.add(session)
    try:
        db.commit()
    except IntegrityError:  # a parallel request won the unique index race (ATT-03)
        db.rollback()
        raise _already_checked_in() from None
    return session, gym


def check_out(db: Session, user: User) -> tuple[AttendanceSession, Gym]:
    expire_stale_sessions(db)
    session = active_session(db, user)
    if session is None:
        raise AppError(409, "not_checked_in", "You are not checked in to any gym.")
    session.check_out_at = utcnow()
    session.close_reason = CloseReason.USER
    db.commit()
    return session, db.get(Gym, session.gym_id)


def current(db: Session, user: User) -> tuple[AttendanceSession, Gym] | None:
    expire_stale_sessions(db)
    session = active_session(db, user)
    if session is None:
        return None
    return session, db.get(Gym, session.gym_id)


def occupancy_counts(db: Session, gym_ids: Iterable[uuid.UUID]) -> dict[uuid.UUID, int]:
    ids = list(gym_ids)
    if not ids:
        return {}
    expire_stale_sessions(db)
    rows = db.execute(
        select(AttendanceSession.gym_id, func.count())
        .where(AttendanceSession.gym_id.in_(ids), AttendanceSession.check_out_at.is_(None))
        .group_by(AttendanceSession.gym_id)
    )
    counts = dict.fromkeys(ids, 0)
    counts.update({gym_id: n for gym_id, n in rows})
    return counts


def occupancy(current_count: int, maximum_capacity: int | None) -> OccupancyOut:
    """GYM-05. Without a configured maximum there is no percentage, just the head count."""
    if not maximum_capacity:
        return OccupancyOut(current=current_count, maximum_capacity=None, percent=None, level=None)
    percent = round(100 * current_count / maximum_capacity)
    level = "low" if percent < 50 else "medium" if percent < 80 else "high"
    return OccupancyOut(
        current=current_count, maximum_capacity=maximum_capacity, percent=percent, level=level
    )
