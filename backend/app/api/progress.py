import uuid

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser
from app.models import WorkoutSession
from app.schemas.progress import (
    ExerciseProgressOut,
    ExerciseSummaryOut,
    ProgressOverviewOut,
    ProgressPointOut,
    RecentRecordOut,
    TopSetOut,
    WeekOut,
)
from app.schemas.training import ExerciseOut
from app.services import progress as progress_service
from app.services.recommendations import uses_weight

router = APIRouter(prefix="/progress", tags=["progress"])


def _top(top) -> TopSetOut:
    return TopSetOut(weight_kg=top.weight_kg, reps=top.reps, date=top.date)


@router.get("", response_model=ExerciseProgressOut)
def exercise_progress(exercise_id: uuid.UUID, db: DB, user: CurrentUser):
    """One exercise over time (US-11): the best set, sets and volume of every workout."""
    h = progress_service.exercise_progress(db, user, exercise_id)
    return ExerciseProgressOut(
        exercise=ExerciseOut.model_validate(h.exercise),
        uses_weight=uses_weight(h.exercise),
        record=_top(h.record) if h.record else None,
        points=[
            ProgressPointOut(
                workout_id=p.workout_id,
                date=p.date,
                weight_kg=p.weight_kg,
                reps=p.reps,
                sets=p.sets,
                volume_kg=p.volume_kg,
                is_record=p.is_record,
            )
            for p in h.sessions
        ],
    )


@router.get("/overview", response_model=ProgressOverviewOut)
def overview(db: DB, user: CurrentUser):
    hs = progress_service.histories(db, user)
    exercises = sorted(hs.values(), key=lambda h: h.sessions[-1].date, reverse=True)
    records = sorted(
        ((h.exercise, p) for h in hs.values() for p in h.sessions if p.is_record),
        key=lambda item: item[1].date,
        reverse=True,
    )[:5]
    total = db.scalar(
        select(func.count()).where(
            WorkoutSession.user_id == user.id, WorkoutSession.ended_at.is_not(None)
        )
    )
    return ProgressOverviewOut(
        total_workouts=total or 0,
        weeks=[WeekOut(**w) for w in progress_service.weekly(db, user)],
        exercises=[
            ExerciseSummaryOut(
                exercise=ExerciseOut.model_validate(h.exercise),
                sessions=len(h.sessions),
                record=_top(h.record),
                last=_top(h.sessions[-1]),
            )
            for h in exercises
        ],
        recent_records=[
            RecentRecordOut(exercise=ExerciseOut.model_validate(e), **_top(p).model_dump())
            for e, p in records
        ],
    )
