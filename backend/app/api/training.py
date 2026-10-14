import uuid

from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas.training import (
    CurrentPlansOut,
    ExerciseOut,
    FitnessProfileIn,
    FitnessProfileOut,
    PlanOut,
    PlanSummaryOut,
)
from app.services import training as training_service

router = APIRouter(tags=["training"])


@router.get("/me/fitness", response_model=FitnessProfileOut | None)
def get_fitness_profile(db: DB, user: CurrentUser):
    """null until the user fills in the profile for the first time."""
    return training_service.get_profile(db, user)


@router.put("/me/fitness", response_model=FitnessProfileOut)
def save_fitness_profile(body: FitnessProfileIn, db: DB, user: CurrentUser):
    return training_service.save_profile(db, user, body)


@router.get("/exercises", response_model=list[ExerciseOut])
def list_exercises(db: DB, _: CurrentUser):
    return training_service.list_exercises(db)


@router.post("/training-plans", status_code=201, response_model=PlanOut)
def generate_plan(db: DB, user: CurrentUser):
    """Propose a new plan from the current profile. It is a draft until accepted."""
    return training_service.plan_out(db, user, training_service.generate_plan(db, user))


@router.get("/training-plans", response_model=list[PlanSummaryOut])
def plan_history(db: DB, user: CurrentUser):
    return training_service.plan_history(db, user)


@router.get("/training-plans/current", response_model=CurrentPlansOut)
def current_plans(db: DB, user: CurrentUser):
    active, draft = training_service.current_plans(db, user)
    return CurrentPlansOut(
        active=training_service.plan_out(db, user, active),
        draft=training_service.plan_out(db, user, draft),
    )


@router.get("/training-plans/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: uuid.UUID, db: DB, user: CurrentUser):
    return training_service.plan_out(db, user, training_service.get_plan(db, user, plan_id))


@router.post("/training-plans/{plan_id}/accept", response_model=PlanOut)
def accept_plan(plan_id: uuid.UUID, db: DB, user: CurrentUser):
    return training_service.plan_out(db, user, training_service.accept_plan(db, user, plan_id))
