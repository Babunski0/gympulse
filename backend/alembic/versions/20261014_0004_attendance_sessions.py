"""attendance sessions

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-14 13:26:20.163520
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attendance_sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("gym_id", sa.Uuid(), nullable=False),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("close_reason", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["gym_id"], ["gyms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_attendance_gym_open", "attendance_sessions", ["gym_id", "check_out_at"], unique=False
    )
    op.create_index(
        "uq_attendance_one_active_per_user",
        "attendance_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("check_out_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_attendance_one_active_per_user",
        table_name="attendance_sessions",
        postgresql_where=sa.text("check_out_at IS NULL"),
    )
    op.drop_index("ix_attendance_gym_open", table_name="attendance_sessions")
    op.drop_table("attendance_sessions")
