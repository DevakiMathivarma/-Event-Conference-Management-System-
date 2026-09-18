from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_session_times_valid"),
        CheckConstraint("capacity > 0", name="ck_session_capacity_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    speaker_id = Column(Integer, ForeignKey("speakers.id", ondelete="SET NULL"), nullable=True)
    hall_id = Column(Integer, ForeignKey("halls.id", ondelete="RESTRICT"), nullable=False)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    capacity = Column(Integer, nullable=False)

    # session_type isn't given a fixed value list in the task - free
    # text like "Keynote", "Workshop", "Panel Discussion"
    session_type = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    event = relationship("Event", back_populates="sessions")
    speaker = relationship("Speaker", back_populates="sessions")
    hall = relationship("Hall", back_populates="sessions")

    bookings = relationship("SessionBooking", back_populates="session", cascade="all, delete-orphan")
    feedback_entries = relationship("Feedback", back_populates="session")# app/models/attendee.py
