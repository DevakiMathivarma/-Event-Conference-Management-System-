from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class PurchaseStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Purchase(Base):
    __tablename__ = "purchases"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_purchase_quantity_positive"),
        CheckConstraint("subtotal >= 0", name="ck_purchase_subtotal_not_negative"),
        CheckConstraint("discount >= 0", name="ck_purchase_discount_not_negative"),
        CheckConstraint("tax >= 0", name="ck_purchase_tax_not_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)

    registration_id = Column(Integer, ForeignKey("registrations.id", ondelete="RESTRICT"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="RESTRICT"), nullable=False)

    quantity = Column(Integer, nullable=False)

    subtotal = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(8, 2), default=0, nullable=False)
    tax = Column(Numeric(8, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)

    status = Column(SQLEnum(PurchaseStatus), default=PurchaseStatus.PENDING, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    registration = relationship("Registration", back_populates="purchases")
    ticket = relationship("Ticket", back_populates="purchases")

    payments = relationship("Payment", back_populates="purchase", cascade="all, delete-orphan")