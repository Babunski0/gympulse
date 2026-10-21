"""Progress over time (LOG-05) and personal records (LOG-06).

Only completed working sets of finished workouts count; warm-ups never do. For exercises with a
weight, a session's "top set" is its heaviest set (most reps breaks a tie) and a record is a heavier
top set, or the same weight for more reps. For bodyweight, timed and cardio exercises it is the
most reps (or seconds/minutes). Nothing is estimated: with no logged sets there is no trend.
"""

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.models import Exercise, PerformedSet, User, WorkoutSession
from app.models._base import utcnow
from app.services.recommendations import uses_weight

WEEKS = 8


@dataclass
class SessionTop:
    workout_id: uuid.UUID
    date: datetime
    weight_kg: float | None
    reps: int
    sets: int = 0
    volume_kg: float = 0.0
    is_record: bool = False


def better(exercise: Exercise, a: SessionTop, b: SessionTop | None) -> bool:
    """Is a strictly better than b?"""
    if b is None:
        return True
    if uses_weight(exercise):
        return (a.weight_kg or 0, a.reps) > (b.weight_kg or 0, b.reps)
    return a.reps > b.reps


@dataclass
class ExerciseHistory:
    exercise: Exercise
    sessions: list[SessionTop] = field(default_factory=list)  # oldest first
    record: SessionTop | None = None


def _working_sets(db: Session, user: User, exercise_id: uuid.UUID | None = None, before=None):
    query = (
        select(PerformedSet, WorkoutSession.id, WorkoutSession.started_at)
        .join(WorkoutSession, WorkoutSession.id == PerformedSet.workout_session_id)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.ended_at.is_not(None),
            PerformedSet.is_completed.is_(True),
            PerformedSet.is_warmup.is_(False),
        )
        .order_by(WorkoutSession.started_at)
    )
    if exercise_id is not None:
        query = query.where(PerformedSet.exercise_id == exercise_id)
    if before is not None:
        query = query.where(WorkoutSession.started_at < before)
    return db.execute(query).all()


def histories(
    db: Session, user: User, exercise_id: uuid.UUID | None = None, before: datetime | None = None
) -> dict[uuid.UUID, ExerciseHistory]:
    rows = _working_sets(db, user, exercise_id, before)
    ids = {s.exercise_id for s, _, _ in rows}
    exercises = {e.id: e for e in db.scalars(select(Exercise).where(Exercise.id.in_(ids)))}
    by_session: dict[tuple[uuid.UUID, uuid.UUID], SessionTop] = {}
    order: dict[uuid.UUID, list[SessionTop]] = defaultdict(list)
    for s, workout_id, started_at in rows:
        exercise = exercises[s.exercise_id]
        weighted = uses_weight(exercise)
        key = (s.exercise_id, workout_id)
        top = by_session.get(key)
        if top is None:
            top = SessionTop(workout_id, started_at, s.weight_kg if weighted else None, s.reps)
            by_session[key] = top
            order[s.exercise_id].append(top)
        elif better(exercise, SessionTop(workout_id, started_at, s.weight_kg, s.reps), top):
            top.weight_kg = s.weight_kg if weighted else None
            top.reps = s.reps
        top.sets += 1
        top.volume_kg += s.reps * s.weight_kg if weighted else 0

    result = {}
    for ex_id, sessions in order.items():
        exercise = exercises[ex_id]
        history = ExerciseHistory(exercise, sessions)
        for top in sessions:
            top.volume_kg = round(top.volume_kg, 1)
            if better(exercise, top, history.record):
                # The very first session sets the bar; it is not a "new" record.
                top.is_record = history.record is not None
                history.record = top
        result[ex_id] = history
    return result


def exercise_progress(db: Session, user: User, exercise_id: uuid.UUID) -> ExerciseHistory:
    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise not_found("exercise")
    return histories(db, user, exercise_id).get(exercise_id) or ExerciseHistory(exercise)


def weekly(db: Session, user: User) -> list[dict]:
    """Workouts and volume for each of the last WEEKS weeks (Monday-Sunday, UTC), oldest first."""
    now = utcnow()
    this_monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    first = this_monday - timedelta(weeks=WEEKS - 1)
    weeks = [
        {"week_start": first + timedelta(weeks=i), "workouts": 0, "volume_kg": 0.0}
        for i in range(WEEKS)
    ]
    workouts = db.scalars(
        select(WorkoutSession).where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.ended_at.is_not(None),
            WorkoutSession.started_at >= first,
        )
    )
    from app.services.workouts import set_volume  # avoid an import cycle

    for w in workouts:
        week = weeks[(w.started_at - first).days // 7]
        week["workouts"] += 1
        week["volume_kg"] += sum(set_volume(s) for s in w.sets)
    for week in weeks:
        week["volume_kg"] = round(week["volume_kg"], 1)
    return weeks
