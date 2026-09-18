from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RegistrationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    ATTENDED = "ATTENDED"


class Registration(Base):
    __tablename__ = "registrations"

    __table_args__ = (
        # prevent duplicate registration - level 6's own business rule,
        # enforced at the database level. one attendee can only have
        # one registration row per event, ever
        UniqueConstraint("attendee_id", "event_id", name="uq_registration_attendee_event"),
    )

    id = Column(Integer, primary_key=True, index=True)

    attendee_id = Column(Integer, ForeignKey("attendees.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="RESTRICT"), nullable=False)

    registration_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    registration_status = Column(SQLEnum(RegistrationStatus), default=RegistrationStatus.PENDING, nullable=False)

    # relationships
    attendee = relationship("Attendee", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")

    purchases = relationship("Purchase", back_populates="registration", cascade="all, delete-orphan")
    session_bookings = relationship("SessionBooking", back_populates="registration", cascade="all, delete-orphan")
    check_in = relationship("CheckIn", back_populates="registration", uselist=False, cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="registration")