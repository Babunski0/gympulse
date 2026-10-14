import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.models.training import EquipmentAccess, Experience, Goal, PlanStatus
from app.schemas.common import ORMModel


class FitnessProfileIn(BaseModel):
    experience_level: Experience
    training_goal: Goal
    days_per_week: Annotated[int, Field(ge=2, le=6)]
    session_minutes: Annotated[int, Field(ge=20, le=150)]
    equipment: EquipmentAccess = EquipmentAccess.GYM
    birth_year: Annotated[int, Field(ge=1920, le=date.today().year - 12)] | None = None
    height_cm: Annotated[int, Field(ge=100, le=250)] | None = None
    weight_kg: Annotated[float, Field(ge=30, le=300)] | None = None


class FitnessProfileOut(ORMModel, FitnessProfileIn):
    updated_at: datetime


class ExerciseOut(ORMModel):
    id: uuid.UUID
    slug: str
    name: str
    muscle_group: str
    movement: str
    equipment: str
    difficulty_level: int
    is_compound: bool
    unit: str
    instructions: str


class PlanExerciseOut(ORMModel):
    id: uuid.UUID
    position: int
    target_sets: int
    rep_min: int
    rep_max: int
    rest_seconds: int
    exercise: ExerciseOut


class PlanDayOut(ORMModel):
    id: uuid.UUID
    day_number: int
    name: str
    exercises: list[PlanExerciseOut]


class PlanSummaryOut(ORMModel):
    id: uuid.UUID
    version: int
    status: PlanStatus
    goal_snapshot: dict
    created_at: datetime
    accepted_at: datetime | None


class PlanOut(PlanSummaryOut):
    notes: list[str]
    generator_version: str
    days: list[PlanDayOut]


class CurrentPlansOut(BaseModel):
    active: PlanOut | None
    draft: PlanOut | None
