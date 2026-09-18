from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating_range"),
    )

    id = Column(Integer, primary_key=True, index=True)

    registration_id = Column(Integer, ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    # nullable - feedback can be about the event overall, or optionally
    # tied to one specific speaker and/or session, matching the task's
    # own field list exactly
    speaker_id = Column(Integer, ForeignKey("speakers.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)

    rating = Column(Integer, nullable=False)
    feedback = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    registration = relationship("Registration")
    event = relationship("Event")
    speaker = relationship("Speaker")
    session = relationship("Session", back_populates="feedback_entries")