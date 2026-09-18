from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CertificateType(str, Enum):
    PARTICIPATION = "PARTICIPATION"
    COMPLETION = "COMPLETION"
    ACHIEVEMENT = "ACHIEVEMENT"


class CertificateStatus(str, Enum):
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)

    # unique, human-readable reference - same auto-generated pattern as
    # every project's policy_number/order_number/claim_number
    certificate_number = Column(String(50), unique=True, nullable=False, index=True)

    # one registration, one certificate - a person shouldn't be able to
    # generate multiple certificates for the same event attendance
    registration_id = Column(Integer, ForeignKey("registrations.id", ondelete="CASCADE"), unique=True, nullable=False)

    attendee_id = Column(Integer, ForeignKey("attendees.id", ondelete="RESTRICT"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="RESTRICT"), nullable=False)

    issue_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # certificate_type isn't given a fixed value list in the task - a
    # reasonable, sensible 3-value set, matching how real event
    # platforms typically distinguish participation vs completion
    certificate_type = Column(SQLEnum(CertificateType), default=CertificateType.PARTICIPATION, nullable=False)

    status = Column(SQLEnum(CertificateStatus), default=CertificateStatus.ISSUED, nullable=False)

    # relationships
    registration = relationship("Registration", back_populates="certificates")
    attendee = relationship("Attendee", back_populates="certificates")
    event = relationship("Event")