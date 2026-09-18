from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PaymentMethod(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)

    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="RESTRICT"), nullable=False)

    # unique transaction reference - the real mechanism behind "prevent
    # duplicate transactions"
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)

    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)

    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    purchase = relationship("Purchase", back_populates="payments")