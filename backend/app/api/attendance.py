from fastapi import APIRouter, Depends

from app.api.deps import DB, CurrentUser
from app.core.rate_limit import rate_limited
from app.models import AttendanceSession, Gym
from app.models._base import utcnow
from app.schemas.attendance import AttendanceOut, CheckInIn, CurrentAttendanceOut
from app.services import attendance as attendance_service

router = APIRouter(prefix="/attendance", tags=["attendance"])


def to_out(session: AttendanceSession, gym: Gym) -> AttendanceOut:
    end = session.check_out_at or utcnow()
    return AttendanceOut(
        id=session.id,
        gym_id=gym.id,
        gym_name=gym.name,
        check_in_at=session.check_in_at,
        check_out_at=session.check_out_at,
        close_reason=session.close_reason,
        auto_close_at=session.check_in_at + attendance_service.max_duration(),
        duration_minutes=int((end - session.check_in_at).total_seconds() // 60),
    )


@router.post(
    "/check-in",
    status_code=201,
    response_model=AttendanceOut,
    dependencies=[Depends(rate_limited("attendance"))],
)
def check_in(body: CheckInIn, db: DB, user: CurrentUser):
    return to_out(*attendance_service.check_in(db, user, body))


@router.post("/check-out", response_model=AttendanceOut)
def check_out(db: DB, user: CurrentUser):
    """Works from anywhere: leaving the radius is not required (US-06)."""
    return to_out(*attendance_service.check_out(db, user))


@router.get("/current", response_model=CurrentAttendanceOut)
def current(db: DB, user: CurrentUser):
    found = attendance_service.current(db, user)
    return CurrentAttendanceOut(session=to_out(*found) if found else None)
