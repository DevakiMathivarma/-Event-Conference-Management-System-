
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Attendee(Base):
    __tablename__ = "attendees"

    id = Column(Integer, primary_key=True, index=True)

    # one login account, one attendee profile - same pattern as every
    # previous project's customer/tenant table
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # organization and designation aren't given fixed value lists in the
    # task - free text like "Acme Corp" and "Senior Developer"
    organization = Column(String(200), nullable=True)
    designation = Column(String(150), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    user = relationship("User", back_populates="attendee", foreign_keys=[user_id])

    registrations = relationship("Registration", back_populates="attendee")
    certificates = relationship("Certificate", back_populates="attendee")