import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._base import IdMixin, created_at_column, utcnow


class Goal(StrEnum):
    STRENGTH = "strength"
    MUSCLE = "muscle"
    ENDURANCE = "endurance"
    FAT_LOSS = "fat_loss"
    GENERAL = "general"


class Experience(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class EquipmentAccess(StrEnum):
    GYM = "gym"  # everything a normal gym has
    DUMBBELLS = "dumbbells"  # dumbbells and bodyweight, e.g. at home
    BODYWEIGHT = "bodyweight"


class PlanStatus(StrEnum):
    DRAFT = "draft"  # a proposal the user has not accepted yet
    ACTIVE = "active"  # the plan the user follows; at most one
    ARCHIVED = "archived"  # earlier versions, kept for history (FIT-06)


class FitnessProfile(Base):
    """One per user (FIT-01..03). Changing it never touches plans or logged workouts."""

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    birth_year: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    experience_level: Mapped[str] = mapped_column(String(20))
    training_goal: Mapped[str] = mapped_column(String(20))
    days_per_week: Mapped[int] = mapped_column(Integer)
    session_minutes: Mapped[int] = mapped_column(Integer)
    equipment: Mapped[str] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Exercise(IdMixin, Base):
    """Curated catalog row; kept in sync with app/services/exercise_catalog.py by slug."""

    __tablename__ = "exercises"

    slug: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    muscle_group: Mapped[str] = mapped_column(String(30))
    movement: Mapped[str] = mapped_column(String(30))
    equipment: Mapped[str] = mapped_column(String(20))
    difficulty_level: Mapped[int] = mapped_column(Integer)  # 1 beginner .. 3 advanced
    is_compound: Mapped[bool] = mapped_column(Boolean)
    unit: Mapped[str] = mapped_column(String(10))  # what "reps" counts: reps, seconds, minutes
    instructions: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TrainingPlan(IdMixin, Base):
    __tablename__ = "training_plans"
    __table_args__ = (UniqueConstraint("user_id", "version"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    goal_snapshot: Mapped[dict] = mapped_column(JSONB)  # the profile this plan was made for
    notes: Mapped[list] = mapped_column(JSONB, default=list)  # adjustments the generator made
    status: Mapped[str] = mapped_column(String(20))
    generator_version: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = created_at_column()
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    days: Mapped[list["PlanDay"]] = relationship(
        order_by="PlanDay.day_number", cascade="all, delete-orphan"
    )


class PlanDay(IdMixin, Base):
    __tablename__ = "plan_days"

    training_plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("training_plans.id", ondelete="CASCADE"), index=True
    )
    day_number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(80))

    exercises: Mapped[list["PlanExercise"]] = relationship(
        order_by="PlanExercise.position", cascade="all, delete-orphan"
    )


class PlanExercise(IdMixin, Base):
    __tablename__ = "plan_exercises"

    plan_day_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("plan_days.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("exercises.id"))
    position: Mapped[int] = mapped_column(Integer)
    target_sets: Mapped[int] = mapped_column(Integer)
    rep_min: Mapped[int] = mapped_column(Integer)
    rep_max: Mapped[int] = mapped_column(Integer)
    rest_seconds: Mapped[int] = mapped_column(Integer)

    exercise: Mapped[Exercise] = relationship(lazy="joined")
