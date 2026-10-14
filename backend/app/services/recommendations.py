"""Suggested weight and reps for an exercise.

Two sources, in order of trust:
1. History: what the user really did last time, with "double progression": once every working
   set reaches the top of the rep range, the weight goes up one step and reps start low again.
2. Estimate: a starting weight from body weight, experience and the exercise, for the first time.
   These are deliberately conservative; the first workout corrects them.

Bodyweight, timed and cardio exercises never get a weight, only reps (or seconds/minutes).
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Exercise, FitnessProfile, PerformedSet, User, WorkoutSession
from app.services.plan_generator import SCHEMES

DEFAULT_BODY_WEIGHT_KG = 75.0

# Typical working weight for ~10 reps, as a share of body weight, for an intermediate lifter.
# Dumbbell values are per dumbbell.
BODY_WEIGHT_SHARE: dict[str, float] = {
    "back-squat": 0.8,
    "romanian-deadlift": 0.7,
    "deadlift": 1.0,
    "hip-thrust": 0.9,
    "bench-press": 0.6,
    "overhead-press": 0.4,
    "barbell-row": 0.55,
    "goblet-squat": 0.22,
    "dumbbell-rdl": 0.22,
    "walking-lunge": 0.12,
    "step-up": 0.1,
    "dumbbell-bench-press": 0.22,
    "incline-dumbbell-press": 0.18,
    "dumbbell-shoulder-press": 0.15,
    "lateral-raise": 0.06,
    "dumbbell-fly": 0.1,
    "overhead-triceps-extension": 0.15,
    "dumbbell-row": 0.25,
    "dumbbell-pullover": 0.15,
    "dumbbell-curl": 0.1,
    "hammer-curl": 0.11,
    "leg-press": 1.3,
    "leg-curl": 0.35,
    "leg-extension": 0.4,
    "calf-raise": 0.7,
    "chest-press-machine": 0.5,
    "cable-fly": 0.12,
    "triceps-pushdown": 0.3,
    "lat-pulldown": 0.6,
    "seated-cable-row": 0.55,
    "face-pull": 0.2,
    "cable-crunch": 0.4,
}
EXPERIENCE_FACTOR = {"beginner": 0.6, "intermediate": 1.0, "advanced": 1.3}
MIN_WEIGHT = {"barbell": 20.0, "dumbbell": 2.0, "machine": 5.0, "cable": 5.0}
LOWER_BODY = {"squat", "hinge", "lunge", "knee_flexion", "knee_extension", "calves"}


@dataclass(frozen=True)
class Recommendation:
    reps: int
    weight_kg: float | None  # None: no weight for this exercise
    per_hand: bool  # weight is per dumbbell
    basis: str  # increase | same | decrease | estimate | bodyweight
    estimated_from_default_weight: bool = False  # no body weight in the profile


def uses_weight(exercise: Exercise) -> bool:
    return exercise.unit == "reps" and exercise.equipment != "bodyweight"


def weight_step(exercise: Exercise, weight: float) -> float:
    if exercise.equipment == "barbell":
        return 5.0 if exercise.movement in LOWER_BODY else 2.5
    if exercise.equipment == "dumbbell":
        return 1.0 if weight < 10 else 2.0
    return 5.0 if weight >= 40 else 2.5


def round_to(value: float, step: float) -> float:
    return round(value / step) * step


def default_range(exercise: Exercise, goal: str | None) -> tuple[int, int]:
    """Rep range when the exercise is not from the plan (a free workout)."""
    if exercise.unit == "seconds":
        return 20, 45
    if exercise.unit == "minutes":
        return 10, 20
    scheme = SCHEMES.get(goal or "general", SCHEMES["general"])[0 if exercise.is_compound else 1]
    return scheme.rep_min, scheme.rep_max


def estimate(
    exercise: Exercise, profile: FitnessProfile | None, rep_min: int, rep_max: int
) -> Recommendation:
    experience = profile.experience_level if profile else "beginner"
    if not uses_weight(exercise):
        reps = rep_min if experience == "beginner" else (rep_min + rep_max) // 2
        return Recommendation(reps=reps, weight_kg=None, per_hand=False, basis="bodyweight")
    body = profile.weight_kg if profile and profile.weight_kg else None
    reps = (rep_min + rep_max) // 2
    share = BODY_WEIGHT_SHARE.get(exercise.slug, 0.2)
    at_ten = (body or DEFAULT_BODY_WEIGHT_KG) * share * EXPERIENCE_FACTOR[experience]
    # Epley: the same effort for fewer reps allows more weight, and the other way around.
    weight = at_ten * (1 + 10 / 30) / (1 + reps / 30)
    weight = max(
        MIN_WEIGHT.get(exercise.equipment, 2.0), round_to(weight, weight_step(exercise, weight))
    )
    return Recommendation(
        reps=reps,
        weight_kg=weight,
        per_hand=exercise.equipment == "dumbbell",
        basis="estimate",
        estimated_from_default_weight=body is None,
    )


def progress(exercise: Exercise, sets: list[PerformedSet], rep_min: int, rep_max: int):
    """Next target from last session's completed working sets."""
    if not uses_weight(exercise):
        best = max(s.reps for s in sets)
        if best >= rep_max:
            return Recommendation(reps=rep_max, weight_kg=None, per_hand=False, basis="increase")
        return Recommendation(reps=best + 1, weight_kg=None, per_hand=False, basis="same")
    top = max(s.weight_kg for s in sets)
    reps_at_top = [s.reps for s in sets if s.weight_kg == top]
    per_hand = exercise.equipment == "dumbbell"
    step = weight_step(exercise, top)
    if min(reps_at_top) >= rep_max:
        return Recommendation(
            reps=rep_min, weight_kg=top + step, per_hand=per_hand, basis="increase"
        )
    if max(reps_at_top) < rep_min - 2 and top - step >= MIN_WEIGHT.get(exercise.equipment, 0):
        return Recommendation(
            reps=rep_min, weight_kg=top - step, per_hand=per_hand, basis="decrease"
        )
    reps = min(max(max(reps_at_top) + 1, rep_min), rep_max)
    return Recommendation(reps=reps, weight_kg=top, per_hand=per_hand, basis="same")


def last_session_sets(
    db: Session, user: User, exercise_ids: list[uuid.UUID], before: WorkoutSession | None = None
) -> dict[uuid.UUID, list[PerformedSet]]:
    """Per exercise: the completed working sets of the most recent finished workout that had it."""
    result: dict[uuid.UUID, list[PerformedSet]] = {}
    if not exercise_ids:
        return result
    query = (
        select(PerformedSet, WorkoutSession.id)
        .join(WorkoutSession, WorkoutSession.id == PerformedSet.workout_session_id)
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.ended_at.is_not(None),
            PerformedSet.exercise_id.in_(exercise_ids),
            PerformedSet.is_completed.is_(True),
            PerformedSet.is_warmup.is_(False),
        )
        .order_by(WorkoutSession.started_at.desc(), PerformedSet.set_number)
    )
    if before is not None:
        query = query.where(
            WorkoutSession.id != before.id, WorkoutSession.started_at < before.started_at
        )
    session_of: dict[uuid.UUID, uuid.UUID] = {}
    for s, workout_id in db.execute(query):
        first = session_of.setdefault(s.exercise_id, workout_id)
        if first == workout_id:
            result.setdefault(s.exercise_id, []).append(s)
    return result


def recommend_many(
    db: Session,
    user: User,
    items: list[tuple[Exercise, int | None, int | None]],
    before: WorkoutSession | None = None,
) -> dict[uuid.UUID, Recommendation]:
    """items: (exercise, rep_min, rep_max); a None range means the goal's default range."""
    profile = db.get(FitnessProfile, user.id)
    goal = profile.training_goal if profile else None
    history = last_session_sets(db, user, [e.id for e, _, _ in items], before)
    out: dict[uuid.UUID, Recommendation] = {}
    for exercise, rep_min, rep_max in items:
        if rep_min is None or rep_max is None:
            rep_min, rep_max = default_range(exercise, goal)
        sets = history.get(exercise.id)
        out[exercise.id] = (
            progress(exercise, sets, rep_min, rep_max)
            if sets
            else estimate(exercise, profile, rep_min, rep_max)
        )
    return out
