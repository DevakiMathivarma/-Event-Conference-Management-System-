from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class SessionBooking(Base):
    __tablename__ = "session_bookings"

    __table_args__ = (
        # prevent duplicate session bookings - level 9's own business
        # rule, enforced at the database level. one registration can
        # only book a given session once, ever
        UniqueConstraint("registration_id", "session_id", name="uq_session_booking_registration_session"),
    )

    id = Column(Integer, primary_key=True, index=True)

    registration_id = Column(Integer, ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)

    booked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    registration = relationship("Registration", back_populates="session_bookings")
    session = relationship("Session", back_populates="bookings")