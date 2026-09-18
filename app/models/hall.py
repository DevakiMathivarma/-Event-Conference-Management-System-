from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class HallAvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class Hall(Base):
    __tablename__ = "halls"

    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_hall_capacity_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    venue_id = Column(Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False)

    hall_name = Column(String(150), nullable=False)
    capacity = Column(Integer, nullable=False)
    floor = Column(Integer, nullable=True)

    availability_status = Column(SQLEnum(HallAvailabilityStatus), default=HallAvailabilityStatus.AVAILABLE, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    venue = relationship("Venue", back_populates="halls")

    sessions = relationship("Session", back_populates="hall")