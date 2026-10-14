import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._base import IdMixin, created_at_column


class WorkoutSession(IdMixin, Base):
    """A logged workout. Independent of gym check-in (LOG-01): it can happen anywhere."""

    __tablename__ = "workout_sessions"
    __table_args__ = (
        # One workout in progress at a time per user.
        Index(
            "uq_workout_one_open_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("ended_at IS NULL"),
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    gym_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("gyms.id", ondelete="SET NULL")
    )
    plan_day_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("plan_days.id", ondelete="SET NULL")
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    sets: Mapped[list["PerformedSet"]] = relationship(
        order_by="(PerformedSet.created_at, PerformedSet.set_number)",
        cascade="all, delete-orphan",
    )


class PerformedSet(IdMixin, Base):
    __tablename__ = "performed_sets"
    __table_args__ = (
        Index("ix_performed_sets_workout_exercise", "workout_session_id", "exercise_id"),
        Index("ix_performed_sets_exercise", "exercise_id"),
    )

    workout_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workout_sessions.id", ondelete="CASCADE")
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("exercises.id"))
    set_number: Mapped[int] = mapped_column(Integer)
    reps: Mapped[int] = mapped_column(Integer)
    weight_kg: Mapped[float] = mapped_column(Float)  # per dumbbell for dumbbell exercises
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_warmup: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at_column()
