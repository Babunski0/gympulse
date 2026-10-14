"""workout log

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-14 16:49:52.081857
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workout_sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("gym_id", sa.Uuid(), nullable=True),
        sa.Column("plan_day_id", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["gym_id"], ["gyms.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_day_id"], ["plan_days.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_workout_sessions_user_id"), "workout_sessions", ["user_id"], unique=False
    )
    op.create_index(
        "uq_workout_one_open_per_user",
        "workout_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )
    op.create_table(
        "performed_sets",
        sa.Column("workout_session_id", sa.Uuid(), nullable=False),
        sa.Column("exercise_id", sa.Uuid(), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False),
        sa.Column("is_warmup", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workout_session_id"], ["workout_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_performed_sets_exercise", "performed_sets", ["exercise_id"], unique=False)
    op.create_index(
        "ix_performed_sets_workout_exercise",
        "performed_sets",
        ["workout_session_id", "exercise_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_performed_sets_workout_exercise", table_name="performed_sets")
    op.drop_index("ix_performed_sets_exercise", table_name="performed_sets")
    op.drop_table("performed_sets")
    op.drop_index(
        "uq_workout_one_open_per_user",
        table_name="workout_sessions",
        postgresql_where=sa.text("ended_at IS NULL"),
    )
    op.drop_index(op.f("ix_workout_sessions_user_id"), table_name="workout_sessions")
    op.drop_table("workout_sessions")
