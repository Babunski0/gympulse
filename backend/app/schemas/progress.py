import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.training import ExerciseOut


class TopSetOut(BaseModel):
    """Best set of one workout; weight_kg is None for bodyweight, timed and cardio exercises."""

    weight_kg: float | None
    reps: int
    date: datetime


class ProgressPointOut(TopSetOut):
    workout_id: uuid.UUID
    sets: int
    volume_kg: float
    is_record: bool  # beat every earlier workout


class ExerciseProgressOut(BaseModel):
    exercise: ExerciseOut
    uses_weight: bool
    record: TopSetOut | None
    points: list[ProgressPointOut]  # oldest first; empty when never logged


class ExerciseSummaryOut(BaseModel):
    exercise: ExerciseOut
    sessions: int
    record: TopSetOut
    last: TopSetOut


class WeekOut(BaseModel):
    week_start: datetime
    workouts: int
    volume_kg: float


class RecentRecordOut(TopSetOut):
    exercise: ExerciseOut


class ProgressOverviewOut(BaseModel):
    total_workouts: int
    weeks: list[WeekOut]  # the last 8 weeks, oldest first
    exercises: list[ExerciseSummaryOut]  # most recently trained first
    recent_records: list[RecentRecordOut]  # newest first, at most 5
