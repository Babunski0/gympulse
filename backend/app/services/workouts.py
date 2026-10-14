"""Workout log (LOG-01..04): start, log sets, correct them, finish, history."""

import uuid
from dataclasses import asdict
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.models import (
    AttendanceSession,
    Exercise,
    FitnessProfile,
    Gym,
    GymMembership,
    PerformedSet,
    PlanDay,
    PlanExercise,
    TrainingPlan,
    User,
    WorkoutSession,
)
from app.models._base import utcnow
from app.models.gym import MembershipStatus
from app.models.training import PlanStatus
from app.schemas.training import ExerciseOut, RecommendationOut
from app.schemas.workouts import (
    HomeSummaryOut,
    NextDayOut,
    PreviousOut,
    SetIn,
    SetOut,
    SetUpdateIn,
    TargetOut,
    WeekOut,
    WorkoutExerciseOut,
    WorkoutOut,
    WorkoutSummaryOut,
)
from app.services.exercise_catalog import sync_catalog
from app.services.recommendations import recommend_many


def set_volume(s: PerformedSet) -> float:
    """Reps x kg for a completed working set; warm-ups and timed exercises do not count."""
    if not s.is_completed or s.is_warmup:
        return 0.0
    return s.reps * s.weight_kg


def get_workout(db: Session, user: User, workout_id: uuid.UUID) -> WorkoutSession:
    workout = db.get(WorkoutSession, workout_id)
    if workout is None or workout.user_id != user.id:
        raise not_found("workout")
    return workout


def open_workout(db: Session, user: User) -> WorkoutSession | None:
    return db.scalar(
        select(WorkoutSession).where(
            WorkoutSession.user_id == user.id, WorkoutSession.ended_at.is_(None)
        )
    )


def last_sets(db: Session, user: User, exercise_ids: list[uuid.UUID], before: WorkoutSession):
    """Per exercise: the heaviest completed working set from the most recent earlier workout."""
    result: dict[uuid.UUID, PreviousOut] = {}
    if not exercise_ids:
        return result
    rows = db.execute(
        select(PerformedSet, WorkoutSession.started_at)
        .join(WorkoutSession, WorkoutSession.id == PerformedSet.workout_session_id)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.id != before.id,
            WorkoutSession.ended_at.is_not(None),
            WorkoutSession.started_at < before.started_at,
            PerformedSet.exercise_id.in_(exercise_ids),
            PerformedSet.is_completed.is_(True),
            PerformedSet.is_warmup.is_(False),
        )
        .order_by(
            WorkoutSession.started_at.desc(),
            PerformedSet.weight_kg.desc(),
            PerformedSet.reps.desc(),
        )
    )
    for s, started_at in rows:
        if s.exercise_id not in result:
            result[s.exercise_id] = PreviousOut(reps=s.reps, weight_kg=s.weight_kg, date=started_at)
    return result


def start_workout(db: Session, user: User, plan_day_id: uuid.UUID | None) -> WorkoutSession:
    plan_day = None
    if plan_day_id is not None:
        plan_day = db.get(PlanDay, plan_day_id)
        plan = plan_day and db.get(TrainingPlan, plan_day.training_plan_id)
        if plan is None or plan.user_id != user.id:
            raise not_found("plan_day")
    if open_workout(db, user) is not None:
        raise AppError(409, "workout_in_progress", "Finish your current workout first.")
    # Logged at the gym the user is checked in to, if any; a workout never requires it.
    visit = db.scalar(
        select(AttendanceSession).where(
            AttendanceSession.user_id == user.id, AttendanceSession.check_out_at.is_(None)
        )
    )
    workout = WorkoutSession(
        user_id=user.id,
        plan_day_id=plan_day.id if plan_day else None,
        gym_id=visit.gym_id if visit else None,
        started_at=utcnow(),
    )
    db.add(workout)
    try:
        db.flush()
    except IntegrityError:  # a parallel start won the unique index race
        db.rollback()
        raise AppError(409, "workout_in_progress", "Finish your current workout first.") from None

    if plan_day is not None:
        # Pre-fill the planned sets with the suggested load so logging is mostly tapping ✓.
        recs = recommend_many(
            db, user, [(pe.exercise, pe.rep_min, pe.rep_max) for pe in plan_day.exercises]
        )
        for pe in plan_day.exercises:
            rec = recs[pe.exercise_id]
            for number in range(1, pe.target_sets + 1):
                db.add(
                    PerformedSet(
                        workout_session_id=workout.id,
                        exercise_id=pe.exercise_id,
                        set_number=number,
                        reps=rec.reps,
                        weight_kg=rec.weight_kg or 0,
                        created_at=workout.started_at,
                    )
                )
    db.commit()
    return workout


def add_set(db: Session, user: User, workout_id: uuid.UUID, data: SetIn) -> PerformedSet:
    workout = get_workout(db, user, workout_id)
    if db.get(Exercise, data.exercise_id) is None:
        raise not_found("exercise")
    number = (
        db.scalar(
            select(func.max(PerformedSet.set_number)).where(
                PerformedSet.workout_session_id == workout.id,
                PerformedSet.exercise_id == data.exercise_id,
            )
        )
        or 0
    ) + 1
    s = PerformedSet(
        workout_session_id=workout.id,
        set_number=number,
        completed_at=utcnow() if data.is_completed else None,
        **data.model_dump(),
    )
    db.add(s)
    db.commit()
    return s


def _get_set(db: Session, user: User, workout_id: uuid.UUID, set_id: uuid.UUID) -> PerformedSet:
    get_workout(db, user, workout_id)
    s = db.get(PerformedSet, set_id)
    if s is None or s.workout_session_id != workout_id:
        raise not_found("set")
    return s


def update_set(
    db: Session, user: User, workout_id: uuid.UUID, set_id: uuid.UUID, data: SetUpdateIn
) -> PerformedSet:
    """LOG-03: corrections are allowed during and after the workout; history uses the new value."""
    s = _get_set(db, user, workout_id, set_id)
    changes = data.model_dump(exclude_none=True)
    for field, value in changes.items():
        setattr(s, field, value)
    if "is_completed" in changes:
        s.completed_at = utcnow() if s.is_completed else None
    db.commit()
    return s


def delete_set(db: Session, user: User, workout_id: uuid.UUID, set_id: uuid.UUID) -> None:
    s = _get_set(db, user, workout_id, set_id)
    db.delete(s)
    db.commit()


def finish_workout(db: Session, user: User, workout_id: uuid.UUID) -> WorkoutSession:
    workout = get_workout(db, user, workout_id)
    if workout.ended_at is not None:
        return workout
    # Planned sets that were never done are not part of what happened.
    for s in list(workout.sets):
        if not s.is_completed:
            workout.sets.remove(s)
    workout.ended_at = utcnow()
    db.commit()
    return workout


def update_notes(db: Session, user: User, workout_id: uuid.UUID, notes: str | None) -> None:
    workout = get_workout(db, user, workout_id)
    workout.notes = notes
    db.commit()


def delete_workout(db: Session, user: User, workout_id: uuid.UUID) -> None:
    db.delete(get_workout(db, user, workout_id))
    db.commit()


def history(db: Session, user: User, limit: int, offset: int) -> list[WorkoutSession]:
    return list(
        db.scalars(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id, WorkoutSession.ended_at.is_not(None))
            .order_by(WorkoutSession.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )


def _names(db: Session, workout: WorkoutSession) -> tuple[str | None, str | None]:
    gym = db.get(Gym, workout.gym_id) if workout.gym_id else None
    day = db.get(PlanDay, workout.plan_day_id) if workout.plan_day_id else None
    return (gym.name if gym else None, day.name if day else None)


def _summary_fields(db: Session, workout: WorkoutSession) -> dict:
    gym_name, day_name = _names(db, workout)
    end = workout.ended_at or utcnow()
    return {
        "id": workout.id,
        "started_at": workout.started_at,
        "ended_at": workout.ended_at,
        "gym_name": gym_name,
        "plan_day_name": day_name,
        "exercise_count": len({s.exercise_id for s in workout.sets}),
        "completed_sets": sum(1 for s in workout.sets if s.is_completed),
        "total_volume_kg": round(sum(set_volume(s) for s in workout.sets), 1),
        "duration_minutes": int((end - workout.started_at).total_seconds() // 60),
    }


def to_summary(db: Session, workout: WorkoutSession) -> WorkoutSummaryOut:
    return WorkoutSummaryOut(**_summary_fields(db, workout))


def to_detail(db: Session, user: User, workout: WorkoutSession) -> WorkoutOut:
    sync_catalog(db)
    targets: dict[uuid.UUID, PlanExercise] = {}
    order: list[uuid.UUID] = []
    if workout.plan_day_id:
        day = db.get(PlanDay, workout.plan_day_id)
        if day:
            for pe in day.exercises:
                targets[pe.exercise_id] = pe
                order.append(pe.exercise_id)
    for s in workout.sets:  # exercises added on the spot come after the planned ones
        if s.exercise_id not in order:
            order.append(s.exercise_id)
    exercises = {e.id: e for e in db.scalars(select(Exercise).where(Exercise.id.in_(order)))}
    previous = last_sets(db, user, order, workout)
    recs = (
        recommend_many(
            db,
            user,
            [
                (
                    exercises[eid],
                    targets[eid].rep_min if eid in targets else None,
                    targets[eid].rep_max if eid in targets else None,
                )
                for eid in order
            ],
            before=workout,
        )
        if workout.ended_at is None
        else {}
    )

    groups = []
    for exercise_id in order:
        sets = sorted(
            (s for s in workout.sets if s.exercise_id == exercise_id), key=lambda s: s.set_number
        )
        if not sets and workout.ended_at is not None:
            continue  # a planned exercise that was skipped
        pe = targets.get(exercise_id)
        groups.append(
            WorkoutExerciseOut(
                exercise=ExerciseOut.model_validate(exercises[exercise_id]),
                target=TargetOut(
                    sets=pe.target_sets,
                    rep_min=pe.rep_min,
                    rep_max=pe.rep_max,
                    rest_seconds=pe.rest_seconds,
                )
                if pe
                else None,
                previous=previous.get(exercise_id),
                recommendation=RecommendationOut(**asdict(recs[exercise_id]))
                if exercise_id in recs
                else None,
                sets=[SetOut.model_validate(s) for s in sets],
            )
        )
    return WorkoutOut(
        **_summary_fields(db, workout),
        plan_day_id=workout.plan_day_id,
        notes=workout.notes,
        exercises=groups,
    )


def home_summary(db: Session, user: User) -> HomeSummaryOut:
    plan = db.scalar(
        select(TrainingPlan).where(
            TrainingPlan.user_id == user.id, TrainingPlan.status == PlanStatus.ACTIVE
        )
    )
    next_day = None
    if plan and plan.days:
        day_ids = [d.id for d in plan.days]
        last_day_id = db.scalar(
            select(WorkoutSession.plan_day_id)
            .where(
                WorkoutSession.user_id == user.id,
                WorkoutSession.ended_at.is_not(None),
                WorkoutSession.plan_day_id.in_(day_ids),
            )
            .order_by(WorkoutSession.started_at.desc())
            .limit(1)
        )
        index = (day_ids.index(last_day_id) + 1) % len(day_ids) if last_day_id else 0
        day = plan.days[index]
        next_day = NextDayOut(
            id=day.id,
            day_number=day.day_number,
            name=day.name,
            exercise_names=[pe.exercise.name for pe in day.exercises],
        )

    now = utcnow()
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week = list(
        db.scalars(
            select(WorkoutSession).where(
                WorkoutSession.user_id == user.id,
                WorkoutSession.ended_at.is_not(None),
                WorkoutSession.started_at >= monday,
            )
        )
    )
    sets = [s for w in week for s in w.sets]
    last = history(db, user, 1, 0)
    return HomeSummaryOut(
        has_profile=db.get(FitnessProfile, user.id) is not None,
        has_active_plan=plan is not None,
        active_gyms=db.scalar(
            select(func.count()).where(
                GymMembership.user_id == user.id, GymMembership.status == MembershipStatus.ACTIVE
            )
        )
        or 0,
        next_day=next_day,
        week=WeekOut(
            workouts=len(week),
            completed_sets=sum(1 for s in sets if s.is_completed),
            total_volume_kg=round(sum(set_volume(s) for s in sets), 1),
        ),
        last_workout=to_summary(db, last[0]) if last else None,
    )
