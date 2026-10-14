import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import IdMixin, created_at_column


class CloseReason(StrEnum):
    USER = "user"
    AUTO_EXPIRED = "auto_expired"


class AttendanceSession(IdMixin, Base):
    """A gym visit. Raw GPS coordinates are deliberately not stored (NFR-02)."""

    __tablename__ = "attendance_sessions"
    __table_args__ = (
        # At most one open session per user, enforced even under concurrent requests (ATT-03).
        Index(
            "uq_attendance_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("check_out_at IS NULL"),
        ),
        Index("ix_attendance_gym_open", "gym_id", "check_out_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    gym_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("gyms.id", ondelete="CASCADE"))
    check_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    close_reason: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = created_at_column()
