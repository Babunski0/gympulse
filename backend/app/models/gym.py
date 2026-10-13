import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import IdMixin, created_at_column


class MembershipStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"


class Gym(IdMixin, Base):
    __tablename__ = "gyms"

    name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(80), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    radius_m: Mapped[int] = mapped_column(Integer)
    maximum_capacity: Mapped[int | None] = mapped_column(Integer)
    membership_requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = created_at_column()


class GymAdmin(IdMixin, Base):
    __tablename__ = "gym_admins"
    __table_args__ = (UniqueConstraint("gym_id", "user_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    gym_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("gyms.id", ondelete="CASCADE"))


class GymMembership(IdMixin, Base):
    __tablename__ = "gym_memberships"
    __table_args__ = (UniqueConstraint("gym_id", "user_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    gym_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("gyms.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = created_at_column()
