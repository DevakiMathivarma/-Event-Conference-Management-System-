from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.common_schema import AppBaseSchema, PaginationResponse


class PaymentCreate(AppBaseSchema):
    payment_method: PaymentMethod
    transaction_id: str = Field(..., min_length=5, max_length=100)


class PaymentResponse(AppBaseSchema):
    id: int
    purchase_id: int
    transaction_id: str
    payment_method: PaymentMethod
    amount: Decimal
    payment_status: PaymentStatus
    payment_date: datetime


class PaymentMessageResponse(AppBaseSchema):
    message: str
    data: PaymentResponse


class PaymentPaginationResponse(AppBaseSchema):
    message: str
    data: list[PaymentResponse]
    pagination: PaginationResponse