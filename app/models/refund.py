
from enum import Enum
from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RefundStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Refund(Base):
    __tablename__ = "refunds"

    __table_args__ = (
        CheckConstraint("refund_amount >= 0", name="ck_refund_amount_not_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # one purchase, one refund - a duplicate refund on the same
    # purchase should never be possible, enforced at the database level
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="CASCADE"), unique=True, nullable=False)

    cancellation_reason = Column(String(300), nullable=True)

    refund_amount = Column(Numeric(10, 2), nullable=False)

    status = Column(SQLEnum(RefundStatus), default=RefundStatus.PENDING, nullable=False)

    refund_date = Column(DateTime(timezone=True), nullable=True)

    processed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    purchase = relationship("Purchase")
    processed_by = relationship("User")