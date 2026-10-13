"""gym city

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-13 13:05:36.938617
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Gyms created before this step get an empty city; the admin fills it in when editing.
    op.add_column(
        "gyms", sa.Column("city", sa.String(length=80), nullable=False, server_default="")
    )
    op.alter_column("gyms", "city", server_default=None)
    op.create_index(op.f("ix_gyms_city"), "gyms", ["city"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_gyms_city"), table_name="gyms")
    op.drop_column("gyms", "city")
