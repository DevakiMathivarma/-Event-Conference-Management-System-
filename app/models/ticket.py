from enum import Enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class TicketType(str, Enum):
    STANDARD = "STANDARD"
    VIP = "VIP"
    EARLY_BIRD = "EARLY_BIRD"
    STUDENT = "STUDENT"


class Ticket(Base):
    __tablename__ = "tickets"

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_ticket_price_not_negative"),
        CheckConstraint("quantity >= 0", name="ck_ticket_quantity_not_negative"),
        CheckConstraint("available_quantity >= 0", name="ck_ticket_available_quantity_not_negative"),
        CheckConstraint("available_quantity <= quantity", name="ck_ticket_available_not_exceeding_total"),
        CheckConstraint("sale_end > sale_start", name="ck_ticket_sale_dates_valid"),
    )

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    ticket_type = Column(SQLEnum(TicketType), nullable=False)
    price = Column(Numeric(8, 2), nullable=False)
    quantity = Column(Integer, nullable=False)

    # tracks how many of this ticket category are still purchasable -
    # the real mechanism behind "sold tickets cannot exceed available
    # quantity." starts equal to quantity, decrements with every real
    # purchase
    available_quantity = Column(Integer, nullable=False)

    sale_start = Column(DateTime(timezone=True), nullable=False)
    sale_end = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # relationships
    event = relationship("Event", back_populates="tickets")

    purchases = relationship("Purchase", back_populates="ticket")