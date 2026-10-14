"""Fitness profile, exercise catalog and versioned training plans (FIT-01..06)."""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError, not_found
from app.models import Exercise, FitnessProfile, PlanDay, PlanExercise, TrainingPlan, User
from app.models._base import utcnow
from app.models.training import PlanStatus
from app.schemas.training import FitnessProfileIn
from app.services import plan_generator
from app.services.exercise_catalog import sync_catalog


def get_profile(db: Session, user: User) -> FitnessProfile | None:
    return db.get(FitnessProfile, user.id)


def save_profile(db: Session, user: User, data: FitnessProfileIn) -> FitnessProfile:
    """Plans and logged workouts are separate rows, so changing the goal never rewrites them."""
    profile = db.get(FitnessProfile, user.id) or FitnessProfile(user_id=user.id)
    for key, value in data.model_dump().items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    return profile


def list_exercises(db: Session) -> list[Exercise]:
    sync_catalog(db)
    return list(
        db.scalars(
            select(Exercise)
            .where(Exercise.is_active.is_(True))
            .order_by(Exercise.muscle_group, Exercise.name)
        )
    )


def _snapshot(profile: FitnessProfile) -> dict:
    return {
        "experience_level": profile.experience_level,
        "training_goal": profile.training_goal,
        "days_per_week": profile.days_per_week,
        "session_minutes": profile.session_minutes,
        "equipment": profile.equipment,
    }


def generate_plan(db: Session, user: User) -> TrainingPlan:
    """A new draft. The active plan stays in place until the user accepts the draft (US-09)."""
    profile = get_profile(db, user)
    if profile is None:
        raise AppError(409, "fitness_profile_required", "Fill in your fitness profile first.")
    sync_catalog(db)
    catalog = [
        plan_generator.CatalogExercise(
            id=e.id,
            slug=e.slug,
            movement=e.movement,
            equipment=e.equipment,
            difficulty_level=e.difficulty_level,
            is_compound=e.is_compound,
            unit=e.unit,
        )
        for e in db.scalars(select(Exercise).where(Exercise.is_active.is_(True)))
    ]
    version = (
        db.scalar(select(func.max(TrainingPlan.version)).where(TrainingPlan.user_id == user.id))
        or 0
    ) + 1
    snapshot = _snapshot(profile)
    try:
        generated = plan_generator.generate(snapshot, catalog, version)
    except plan_generator.PlanGenerationError:
        raise AppError(
            422,
            "plan_generation_failed",
            "Could not build a plan for this profile. Your current plan is unchanged.",
        ) from None

    # Only one open proposal at a time; the previous one goes to history.
    db.execute(
        update(TrainingPlan)
        .where(TrainingPlan.user_id == user.id, TrainingPlan.status == PlanStatus.DRAFT)
        .values(status=PlanStatus.ARCHIVED)
    )
    plan = TrainingPlan(
        user_id=user.id,
        version=version,
        goal_snapshot=snapshot,
        notes=generated.notes,
        status=PlanStatus.DRAFT,
        generator_version=plan_generator.GENERATOR_VERSION,
        days=[
            PlanDay(
                day_number=number,
                name=day.name,
                exercises=[
                    PlanExercise(
                        exercise_id=item.exercise.id,
                        position=position,
                        target_sets=item.sets,
                        rep_min=item.rep_min,
                        rep_max=item.rep_max,
                        rest_seconds=item.rest_seconds,
                    )
                    for position, item in enumerate(day.exercises, start=1)
                ],
            )
            for number, day in enumerate(generated.days, start=1)
        ],
    )
    db.add(plan)
    db.commit()
    return get_plan(db, user, plan.id)


def get_plan(db: Session, user: User, plan_id: uuid.UUID) -> TrainingPlan:
    plan = db.get(TrainingPlan, plan_id)
    if plan is None or plan.user_id != user.id:
        raise not_found("training_plan")
    return plan


def _plan_with_status(db: Session, user: User, status: PlanStatus) -> TrainingPlan | None:
    return db.scalar(
        select(TrainingPlan)
        .where(TrainingPlan.user_id == user.id, TrainingPlan.status == status)
        .order_by(TrainingPlan.version.desc())
        .limit(1)
    )


def current_plans(db: Session, user: User) -> tuple[TrainingPlan | None, TrainingPlan | None]:
    return (
        _plan_with_status(db, user, PlanStatus.ACTIVE),
        _plan_with_status(db, user, PlanStatus.DRAFT),
    )


def accept_plan(db: Session, user: User, plan_id: uuid.UUID) -> TrainingPlan:
    plan = get_plan(db, user, plan_id)
    if plan.status == PlanStatus.ACTIVE:
        return plan
    db.execute(
        update(TrainingPlan)
        .where(TrainingPlan.user_id == user.id, TrainingPlan.status == PlanStatus.ACTIVE)
        .values(status=PlanStatus.ARCHIVED)
    )
    plan.status = PlanStatus.ACTIVE
    plan.accepted_at = utcnow()
    db.commit()
    return plan


def plan_history(db: Session, user: User) -> list[TrainingPlan]:
    return list(
        db.scalars(
            select(TrainingPlan)
            .where(TrainingPlan.user_id == user.id)
            .order_by(TrainingPlan.version.desc())
        )
    )
