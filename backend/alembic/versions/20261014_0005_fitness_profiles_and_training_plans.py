"""fitness profiles and training plans

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-14 16:32:25.961685
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "exercises",
        sa.Column("slug", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("muscle_group", sa.String(length=30), nullable=False),
        sa.Column("movement", sa.String(length=30), nullable=False),
        sa.Column("equipment", sa.String(length=20), nullable=False),
        sa.Column("difficulty_level", sa.Integer(), nullable=False),
        sa.Column("is_compound", sa.Boolean(), nullable=False),
        sa.Column("unit", sa.String(length=10), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "training_plans",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("goal_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("generator_version", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "version"),
    )
    op.create_index(op.f("ix_training_plans_user_id"), "training_plans", ["user_id"], unique=False)
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("experience_level", sa.String(length=20), nullable=False),
        sa.Column("training_goal", sa.String(length=20), nullable=False),
        sa.Column("days_per_week", sa.Integer(), nullable=False),
        sa.Column("session_minutes", sa.Integer(), nullable=False),
        sa.Column("equipment", sa.String(length=20), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "plan_days",
        sa.Column("training_plan_id", sa.Uuid(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["training_plan_id"], ["training_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plan_days_training_plan_id"), "plan_days", ["training_plan_id"], unique=False
    )
    op.create_table(
        "plan_exercises",
        sa.Column("plan_day_id", sa.Uuid(), nullable=False),
        sa.Column("exercise_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("target_sets", sa.Integer(), nullable=False),
        sa.Column("rep_min", sa.Integer(), nullable=False),
        sa.Column("rep_max", sa.Integer(), nullable=False),
        sa.Column("rest_seconds", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["exercise_id"],
            ["exercises.id"],
        ),
        sa.ForeignKeyConstraint(["plan_day_id"], ["plan_days.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_plan_exercises_plan_day_id"), "plan_exercises", ["plan_day_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_plan_exercises_plan_day_id"), table_name="plan_exercises")
    op.drop_table("plan_exercises")
    op.drop_index(op.f("ix_plan_days_training_plan_id"), table_name="plan_days")
    op.drop_table("plan_days")
    op.drop_table("user_profiles")
    op.drop_index(op.f("ix_training_plans_user_id"), table_name="training_plans")
    op.drop_table("training_plans")
    op.drop_table("exercises")
