from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CheckInMethod(str, Enum):
    QR_CODE = "QR_CODE"
    MANUAL = "MANUAL"
    STAFF = "STAFF"


class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True)

    # one registration, one check-in record - matching the model's own
    # uselist=False on the registration side, this is the real
    # database-level backing for "duplicate check-in must be prevented"
    registration_id = Column(Integer, ForeignKey("registrations.id", ondelete="CASCADE"), unique=True, nullable=False)

    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)

    check_in_method = Column(SQLEnum(CheckInMethod), nullable=True)

    checked_in_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    registration = relationship("Registration", back_populates="check_in")
    checked_in_by = relationship("User")