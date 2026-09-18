from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.models.purchase import PurchaseStatus
from app.schemas.common_schema import AppBaseSchema


class PurchaseCreate(AppBaseSchema):
    registration_id: int
    quantity: int = Field(..., gt=0)


class PurchaseResponse(AppBaseSchema):
    id: int
    registration_id: int
    ticket_id: int
    quantity: int
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total_amount: Decimal
    status: PurchaseStatus
    created_at: datetime


class PurchaseMessageResponse(AppBaseSchema):
    message: str
    data: PurchaseResponse