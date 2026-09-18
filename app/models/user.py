from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    EVENT_ORGANIZER = "EVENT_ORGANIZER"
    SPEAKER = "SPEAKER"
    STAFF = "STAFF"
    ATTENDEE = "ATTENDEE"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.ATTENDEE)

    #- account activation/deactivation
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # a speaker-role user has exactly one speaker profile 
    speaker = relationship("Speaker", back_populates="user", uselist=False, foreign_keys="Speaker.user_id")

    # an attendee-role user has exactly one attendee profile
    attendee = relationship("Attendee", back_populates="user", uselist=False, foreign_keys="Attendee.user_id")