"""gyms and memberships

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-13 12:50:34.348583
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gyms",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("radius_m", sa.Integer(), nullable=False),
        sa.Column("maximum_capacity", sa.Integer(), nullable=True),
        sa.Column("membership_requires_approval", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "gym_admins",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("gym_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["gym_id"], ["gyms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gym_id", "user_id"),
    )
    op.create_table(
        "gym_memberships",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("gym_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["gym_id"], ["gyms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gym_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("gym_memberships")
    op.drop_table("gym_admins")
    op.drop_table("gyms")
