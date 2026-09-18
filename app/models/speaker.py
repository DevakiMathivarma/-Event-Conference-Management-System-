from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Speaker(Base):
    __tablename__ = "speakers"

    id = Column(Integer, primary_key=True, index=True)

    # one login account, one speaker profile - same one-to-one pattern
    # as every other profile table across every project
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    bio = Column(Text, nullable=True)

    # expertise isn't given a fixed value list in the task - free text
    # like "Machine Learning, Cloud Architecture"
    expertise = Column(String(300), nullable=True)

    company = Column(String(200), nullable=True)

    # in years - a plain integer, matching the task's own simple field name
    experience = Column(Integer, nullable=True)

    # a speaker profile can be deactivated independently of their login
    # account - the real mechanism behind "inactive speakers cannot be
    # assigned." this is deliberately separate from User.is_active,
    # since a speaker could still log in and update their own profile
    # even while temporarily marked unavailable for new assignments
    is_active = Column(Boolean, default=True, nullable=False)

    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    user = relationship("User", back_populates="speaker", foreign_keys=[user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    sessions = relationship("Session", back_populates="speaker")