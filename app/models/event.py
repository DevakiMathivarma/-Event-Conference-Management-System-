# app/models/event.py

from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class EventType(str, Enum):
    CONFERENCE = "CONFERENCE"
    WORKSHOP = "WORKSHOP"
    SEMINAR = "SEMINAR"
    MEETUP = "MEETUP"
    TRAINING = "TRAINING"


class EventStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Event(Base):
    __tablename__ = "events"

    __table_args__ = (
        CheckConstraint("end_date > start_date", name="ck_event_dates_valid"),
        CheckConstraint("registration_end <= start_date", name="ck_event_registration_closes_before_start"),
        CheckConstraint("capacity > 0", name="ck_event_capacity_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    event_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(SQLEnum(EventType), nullable=False)

    organizer_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    registration_start = Column(DateTime(timezone=True), nullable=False)
    registration_end = Column(DateTime(timezone=True), nullable=False)

    capacity = Column(Integer, nullable=False)

    status = Column(SQLEnum(EventStatus), default=EventStatus.DRAFT, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    organizer = relationship("User")

    sessions = relationship("Session", back_populates="event", cascade="all, delete-orphan")
    registrations = relationship("Registration", back_populates="event")
    tickets = relationship("Ticket", back_populates="event", cascade="all, delete-orphan")