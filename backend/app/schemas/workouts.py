import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.training import ExerciseOut

# Reps also count seconds (plank) or minutes (cardio), hence the generous upper bound.
Reps = Annotated[int, Field(ge=0, le=1000)]
WeightKg = Annotated[float, Field(ge=0, le=1000)]  # US-10: negative weight is rejected


class WorkoutStartIn(BaseModel):
    plan_day_id: uuid.UUID | None = None  # None: a free workout without a plan


class SetIn(BaseModel):
    exercise_id: uuid.UUID
    reps: Reps = 0
    weight_kg: WeightKg = 0
    is_completed: bool = False
    is_warmup: bool = False


class SetUpdateIn(BaseModel):
    reps: Reps | None = None
    weight_kg: WeightKg | None = None
    is_completed: bool | None = None
    is_warmup: bool | None = None


class WorkoutUpdateIn(BaseModel):
    notes: Annotated[str, Field(max_length=2000)] | None = None


class SetOut(ORMModel):
    id: uuid.UUID
    exercise_id: uuid.UUID
    set_number: int
    reps: int
    weight_kg: float
    is_completed: bool
    is_warmup: bool
    completed_at: datetime | None


class TargetOut(BaseModel):
    sets: int
    rep_min: int
    rep_max: int
    rest_seconds: int


class PreviousOut(BaseModel):
    """The best completed set of this exercise in the user's last finished workout."""

    reps: int
    weight_kg: float
    date: datetime


class WorkoutExerciseOut(BaseModel):
    exercise: ExerciseOut
    target: TargetOut | None
    previous: PreviousOut | None
    sets: list[SetOut]


class WorkoutSummaryOut(BaseModel):
    id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None
    gym_name: str | None
    plan_day_name: str | None
    exercise_count: int
    completed_sets: int
    total_volume_kg: float  # sum of reps x kg over completed working sets
    duration_minutes: int


class WorkoutOut(WorkoutSummaryOut):
    plan_day_id: uuid.UUID | None
    notes: str | None
    exercises: list[WorkoutExerciseOut]


class CurrentWorkoutOut(BaseModel):
    workout: WorkoutOut | None
