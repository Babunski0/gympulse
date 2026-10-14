import uuid

from fastapi import APIRouter, Query

from app.api.deps import DB, CurrentUser
from app.schemas.workouts import (
    CurrentWorkoutOut,
    HomeSummaryOut,
    SetIn,
    SetOut,
    SetUpdateIn,
    WorkoutOut,
    WorkoutStartIn,
    WorkoutSummaryOut,
    WorkoutUpdateIn,
)
from app.services import workouts as workout_service

router = APIRouter(prefix="/workouts", tags=["workouts"])
summary_router = APIRouter(tags=["workouts"])


@summary_router.get("/me/summary", response_model=HomeSummaryOut)
def home_summary(db: DB, user: CurrentUser):
    """Next plan day, this week's numbers and the last workout, for the home screen."""
    return workout_service.home_summary(db, user)


@router.post("", status_code=201, response_model=WorkoutOut)
def start_workout(body: WorkoutStartIn, db: DB, user: CurrentUser):
    """Start from a plan day (sets pre-filled from last time) or as a free workout."""
    workout = workout_service.start_workout(db, user, body.plan_day_id)
    return workout_service.to_detail(db, user, workout)


@router.get("/current", response_model=CurrentWorkoutOut)
def current_workout(db: DB, user: CurrentUser):
    workout = workout_service.open_workout(db, user)
    return CurrentWorkoutOut(
        workout=workout_service.to_detail(db, user, workout) if workout else None
    )


@router.get("", response_model=list[WorkoutSummaryOut])
def workout_history(
    db: DB,
    user: CurrentUser,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return [
        workout_service.to_summary(db, w) for w in workout_service.history(db, user, limit, offset)
    ]


@router.get("/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: uuid.UUID, db: DB, user: CurrentUser):
    workout = workout_service.get_workout(db, user, workout_id)
    return workout_service.to_detail(db, user, workout)


@router.patch("/{workout_id}", status_code=204)
def update_workout(workout_id: uuid.UUID, body: WorkoutUpdateIn, db: DB, user: CurrentUser):
    workout_service.update_notes(db, user, workout_id, body.notes)


@router.post("/{workout_id}/finish", response_model=WorkoutOut)
def finish_workout(workout_id: uuid.UUID, db: DB, user: CurrentUser):
    workout = workout_service.finish_workout(db, user, workout_id)
    return workout_service.to_detail(db, user, workout)


@router.delete("/{workout_id}", status_code=204)
def delete_workout(workout_id: uuid.UUID, db: DB, user: CurrentUser):
    workout_service.delete_workout(db, user, workout_id)


@router.post("/{workout_id}/sets", status_code=201, response_model=SetOut)
def add_set(workout_id: uuid.UUID, body: SetIn, db: DB, user: CurrentUser):
    return workout_service.add_set(db, user, workout_id, body)


@router.patch("/{workout_id}/sets/{set_id}", response_model=SetOut)
def update_set(
    workout_id: uuid.UUID, set_id: uuid.UUID, body: SetUpdateIn, db: DB, user: CurrentUser
):
    return workout_service.update_set(db, user, workout_id, set_id, body)


@router.delete("/{workout_id}/sets/{set_id}", status_code=204)
def delete_set(workout_id: uuid.UUID, set_id: uuid.UUID, db: DB, user: CurrentUser):
    workout_service.delete_set(db, user, workout_id, set_id)
