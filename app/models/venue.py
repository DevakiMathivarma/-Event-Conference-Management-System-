from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class VenueStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Venue(Base):
    __tablename__ = "venues"

    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_venue_capacity_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    venue_name = Column(String(200), nullable=False)
    address = Column(String(300), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    capacity = Column(Integer, nullable=False)

    # facilities isn't given a fixed value list in the task - free text
    # like "Wi-Fi, Parking, Catering, AV Equipment"
    facilities = Column(Text, nullable=True)

    status = Column(SQLEnum(VenueStatus), default=VenueStatus.ACTIVE, nullable=False)

    # tracks who actually created this venue - either admin or an event
    # organizer, matching our earlier decision that both can create venues
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    created_by = relationship("User")

    halls = relationship("Hall", back_populates="venue", cascade="all, delete-orphan")